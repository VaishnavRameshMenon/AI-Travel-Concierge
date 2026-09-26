from unittest.mock import MagicMock, patch
import pytest
from pydantic import BaseModel

from backend.app.agent.llm import ResilientStructuredLLM, is_retriable_error


class SampleOutput(BaseModel):
    summary: str
    budget: float


def test_is_retriable_error_identifies_transient_failures():
    """Verify that transient server, capacity, and rate limit errors are classified as retriable."""
    assert is_retriable_error(Exception("503 Server Error: Service Unavailable"))
    assert is_retriable_error(Exception("google.genai.errors.ServerError: UNAVAILABLE"))
    assert is_retriable_error(Exception("This model is currently experiencing high demand."))
    assert is_retriable_error(Exception("ResourceExhausted: 429 Rate limit exceeded"))
    assert is_retriable_error(Exception("ReadTimeout: Request timed out"))
    assert not is_retriable_error(ValueError("Invalid argument provided to parser"))
    assert not is_retriable_error(KeyError("missing_key"))


def test_resilient_llm_succeeds_on_first_attempt():
    """Verify clean return when the primary model succeeds immediately."""
    llm_wrapper = ResilientStructuredLLM(
        schema=SampleOutput,
        primary_model="gemini-3.6-flash",
        fallback_models=["gemini-2.5-flash"],
        max_retries_per_model=2,
        base_delay=0.01,
    )

    expected = SampleOutput(summary="Great trip", budget=50000.0)
    mock_runnable = MagicMock()
    mock_runnable.invoke.return_value = expected

    with patch.object(llm_wrapper, "_build_runnable", return_value=mock_runnable):
        result = llm_wrapper.invoke("Plan a trip")

    assert result == expected
    assert mock_runnable.invoke.call_count == 1


def test_resilient_llm_retries_and_recovers_on_transient_error():
    """Verify that a transient 503 error on the first attempt triggers retry with backoff and succeeds."""
    llm_wrapper = ResilientStructuredLLM(
        schema=SampleOutput,
        primary_model="gemini-3.6-flash",
        fallback_models=["gemini-2.5-flash"],
        max_retries_per_model=3,
        base_delay=0.01,  # Fast backoff for tests
    )

    expected = SampleOutput(summary="Recovered plan", budget=75000.0)
    mock_runnable = MagicMock()
    # First call throws 503, second call succeeds
    mock_runnable.invoke.side_effect = [
        Exception("503 UNAVAILABLE: Model experiencing high demand"),
        expected,
    ]

    with patch.object(llm_wrapper, "_build_runnable", return_value=mock_runnable):
        result = llm_wrapper.invoke("Plan a trip")

    assert result == expected
    assert mock_runnable.invoke.call_count == 2


def test_resilient_llm_falls_back_to_secondary_model():
    """Verify that exhausting retries on the primary model seamlessly switches to the fallback model."""
    llm_wrapper = ResilientStructuredLLM(
        schema=SampleOutput,
        primary_model="gemini-3.6-flash",
        fallback_models=["gemini-2.5-flash"],
        max_retries_per_model=2,
        base_delay=0.01,
    )

    expected = SampleOutput(summary="Fallback model plan", budget=60000.0)

    primary_mock = MagicMock()
    primary_mock.invoke.side_effect = Exception("503 UNAVAILABLE: Spikes in demand")

    fallback_mock = MagicMock()
    fallback_mock.invoke.return_value = expected

    def mock_builder(model_name):
        if model_name == "gemini-3.6-flash":
            return primary_mock
        return fallback_mock

    with patch.object(llm_wrapper, "_build_runnable", side_effect=mock_builder):
        result = llm_wrapper.invoke("Plan a trip")

    assert result == expected
    assert primary_mock.invoke.call_count == 2
    assert fallback_mock.invoke.call_count == 1
