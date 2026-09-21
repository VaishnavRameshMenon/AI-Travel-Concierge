import pytest
from pydantic import ValidationError

from backend.app.api.schemas import TripGenerationRequest


def test_trip_request_requires_meaningful_query():
    with pytest.raises(ValidationError):
        TripGenerationRequest(user_query="hi")


def test_trip_request_accepts_natural_language():
    request = TripGenerationRequest(user_query="Plan a three day trip to Tokyo")
    assert request.user_query.startswith("Plan")
