import os
import random
import time
from typing import Any, Type

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel

from backend.app.monitoring.logger import logger


load_dotenv()


PRIMARY_MODEL = "gemini-3.6-flash"

FALLBACK_MODELS = [
    "gemini-2.5-flash",
    "gemini-1.5-flash",
]


# Keep the original primary LLM instance available for compatibility.
#
# max_retries=0 is intentional:
# LangChain should not independently spend extra time retrying a request
# that our resilience layer is already handling.
llm = ChatGoogleGenerativeAI(
    model=PRIMARY_MODEL,
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0,
    max_retries=0,
)


def _error_text(exc: Exception) -> str:
    """Return a normalized lowercase error string."""
    return str(exc).lower()


def is_daily_quota_exhausted(exc: Exception) -> bool:
    """
    Detect Gemini errors indicating that the project's daily quota is
    exhausted.

    Daily quota exhaustion should NOT be retried repeatedly because the
    request cannot succeed until the quota resets or the project tier/quota
    changes.
    """
    msg = _error_text(exc)

    daily_quota_patterns = [
        "generate_requests_per_day_per_project_per_model",
        "generaterequestsperdayperprojectpermodelfreetier",
        "generate_content_free_tier_requests",
        "quota_exceeded",
        "quota exceeded",
        "daily quota",
        "perday",
        "retry in 17h",
        "retry in 18h",
        "retry in 19h",
        "retry in 20h",
        "retry in 21h",
        "retry in 22h",
        "retry in 23h",
    ]

    return any(pattern in msg for pattern in daily_quota_patterns)


def is_retriable_error(exc: Exception) -> bool:
    """
    Check whether an exception represents a temporary failure.

    Important:
    Daily quota exhaustion is explicitly excluded from retry handling.
    """
    if is_daily_quota_exhausted(exc):
        return False

    msg = _error_text(exc)

    retriable_patterns = [
        "503",
        "unavailable",
        "429",
        "too many requests",
        "rate limit",
        "rate_limit",
        "rate_limit_exceeded",
        "timeout",
        "timed out",
        "500",
        "502",
        "504",
        "server error",
        "servererror",
        "temporary",
        "connection reset",
        "connection closed",
        "disconnect",
        "overloaded",
        "high demand",
        "resourceexhausted",
    ]

    return any(pattern in msg for pattern in retriable_patterns)


class ResilientStructuredLLM:
    """
    Structured Gemini LLM wrapper with:

    - primary model
    - fallback models
    - controlled retries for temporary failures
    - immediate handling of exhausted daily quotas
    - no duplicate SDK-level retry storm
    """

    def __init__(
        self,
        schema: Type[BaseModel],
        primary_model: str = PRIMARY_MODEL,
        fallback_models: list[str] | None = None,
        max_retries_per_model: int = 2,
        base_delay: float = 1.0,
    ):
        self.schema = schema
        self.primary_model = primary_model

        self.fallback_models = (
            fallback_models
            if fallback_models is not None
            else FALLBACK_MODELS
        )

        # Keep model order deterministic and remove duplicates.
        seen = set()
        self.models: list[str] = []

        for model_name in [self.primary_model] + self.fallback_models:
            if model_name and model_name not in seen:
                seen.add(model_name)
                self.models.append(model_name)

        self.max_retries_per_model = max(1, max_retries_per_model)
        self.base_delay = base_delay

    def _build_runnable(self, model_name: str) -> Any:
        """
        Build a structured-output Gemini runnable.

        max_retries=0 prevents the underlying client from creating another
        hidden retry loop on top of this wrapper.
        """
        client = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=os.getenv("GEMINI_API_KEY"),
            temperature=0,
            max_retries=0,
        )

        return client.with_structured_output(self.schema)

    def invoke(self, prompt: Any, **kwargs) -> Any:
        last_exception: Exception | None = None

        for model_idx, model_name in enumerate(self.models):
            runnable = self._build_runnable(model_name)

            is_fallback = model_idx > 0

            if is_fallback:
                logger.info(
                    "llm_using_fallback_model",
                    model=model_name,
                    primary_model=self.primary_model,
                )

            for attempt in range(self.max_retries_per_model):
                try:
                    return runnable.invoke(prompt, **kwargs)

                except Exception as exc:
                    last_exception = exc

                    # --------------------------------------------------
                    # DAILY QUOTA EXHAUSTED
                    # --------------------------------------------------
                    #
                    # Do NOT retry this model.
                    #
                    # The Google API explicitly reports daily quota
                    # exhaustion separately from temporary rate limiting.
                    # Retrying repeatedly only wastes time and requests.
                    #
                    if is_daily_quota_exhausted(exc):
                        logger.error(
                            "llm_daily_quota_exhausted",
                            model=model_name,
                            error=str(exc)[:500],
                            fallback_available=(
                                model_idx < len(self.models) - 1
                            ),
                        )

                        # Immediately move to the next model.
                        break

                    retriable = is_retriable_error(exc)

                    # --------------------------------------------------
                    # NON-RETRIABLE ERROR
                    # --------------------------------------------------
                    if not retriable:
                        logger.error(
                            "llm_non_retriable_error",
                            model=model_name,
                            error=str(exc)[:500],
                        )

                        break

                    # --------------------------------------------------
                    # TEMPORARY ERROR
                    # --------------------------------------------------
                    if attempt < self.max_retries_per_model - 1:
                        delay = min(
                            self.base_delay * (2**attempt)
                            + random.uniform(0.1, 0.5),
                            8.0,
                        )

                        logger.warning(
                            "llm_call_temporary_failure_retrying",
                            model=model_name,
                            attempt=attempt + 1,
                            max_retries=self.max_retries_per_model,
                            delay_seconds=round(delay, 2),
                            error=str(exc)[:300],
                        )

                        time.sleep(delay)

                    else:
                        logger.warning(
                            "llm_model_retries_exhausted",
                            model=model_name,
                            attempts=attempt + 1,
                            fallback_available=(
                                model_idx < len(self.models) - 1
                            ),
                            error=str(exc)[:300],
                        )

                        break

            # ----------------------------------------------------------
            # FALLBACK MODEL
            # ----------------------------------------------------------

            if model_idx < len(self.models) - 1:
                next_model = self.models[model_idx + 1]

                logger.warning(
                    "llm_switching_to_fallback_model",
                    previous_model=model_name,
                    next_model=next_model,
                )

        # Nothing succeeded.
        if last_exception is not None:
            raise last_exception

        raise RuntimeError(
            "No LLM models available to invoke."
        )


def get_resilient_structured_llm(
    schema: Type[BaseModel],
) -> ResilientStructuredLLM:
    """Factory for the resilient structured LLM."""
    return ResilientStructuredLLM(schema=schema)