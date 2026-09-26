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
FALLBACK_MODELS = ["gemini-2.5-flash", "gemini-1.5-flash"]

# Keep the original primary LLM instance unchanged for compatibility
llm = ChatGoogleGenerativeAI(
    model=PRIMARY_MODEL,
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0,
)


def is_retriable_error(exc: Exception) -> bool:
    """Check if an exception represents a temporary error suitable for retry."""
    msg = str(exc).lower()
    retriable_patterns = [
        "503",
        "unavailable",
        "resourceexhausted",
        "429",
        "high demand",
        "rate limit",
        "rate_limit",
        "quota",
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
    ]
    return any(p in msg for p in retriable_patterns)


class ResilientStructuredLLM:
    """
    Wraps structured output generation with retry, exponential backoff,
    and automatic fallback to alternative Gemini models if the primary model fails.
    """

    def __init__(
        self,
        schema: Type[BaseModel],
        primary_model: str = PRIMARY_MODEL,
        fallback_models: list[str] | None = None,
        max_retries_per_model: int = 3,
        base_delay: float = 1.0,
    ):
        self.schema = schema
        self.primary_model = primary_model
        self.fallback_models = fallback_models if fallback_models is not None else FALLBACK_MODELS
        # Distinct model sequence starting with the primary model
        seen = set()
        self.models: list[str] = []
        for m in [self.primary_model] + self.fallback_models:
            if m and m not in seen:
                seen.add(m)
                self.models.append(m)
        self.max_retries_per_model = max_retries_per_model
        self.base_delay = base_delay

    def _build_runnable(self, model_name: str) -> Any:
        client = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=os.getenv("GEMINI_API_KEY"),
            temperature=0,
        )
        return client.with_structured_output(self.schema)

    def invoke(self, prompt: Any, **kwargs) -> Any:
        last_exception: Exception | None = None

        for model_idx, model_name in enumerate(self.models):
            runnable = self._build_runnable(model_name)
            is_fallback = model_idx > 0

            for attempt in range(self.max_retries_per_model):
                try:
                    return runnable.invoke(prompt, **kwargs)
                except Exception as exc:
                    last_exception = exc
                    retriable = is_retriable_error(exc)

                    if not retriable and attempt == 0:
                        # Non-retriable client-side error: try next model or re-raise
                        logger.warning(
                            "llm_non_retriable_error",
                            model=model_name,
                            error=str(exc)[:200],
                        )
                        break

                    if attempt < self.max_retries_per_model - 1 and retriable:
                        delay = min(
                            self.base_delay * (2 ** attempt) + random.uniform(0.1, 0.5),
                            8.0,
                        )
                        logger.warning(
                            "llm_call_temporary_failure_retrying",
                            model=model_name,
                            attempt=attempt + 1,
                            max_retries=self.max_retries_per_model,
                            delay_seconds=round(delay, 2),
                            error=str(exc)[:200],
                        )
                        time.sleep(delay)
                    else:
                        logger.warning(
                            "llm_model_retries_exhausted",
                            model=model_name,
                            attempts=attempt + 1,
                            fallback_available=model_idx < len(self.models) - 1,
                            error=str(exc)[:200],
                        )
                        break

            # If this was not the last model in the chain, log fallback transition
            if model_idx < len(self.models) - 1:
                next_model = self.models[model_idx + 1]
                logger.warning(
                    "llm_switching_to_fallback_model",
                    previous_model=model_name,
                    next_model=next_model,
                )

        if last_exception is not None:
            raise last_exception
        raise RuntimeError("No LLM models available to invoke.")


def get_resilient_structured_llm(schema: Type[BaseModel]) -> ResilientStructuredLLM:
    """Factory for resilient structured LLM with retry and model fallback."""
    return ResilientStructuredLLM(schema=schema)