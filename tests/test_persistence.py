"""Deterministic tests for Trip persistence and GET /trips/{trip_id} response.

All tests use an in-memory SQLite database – no live Gemini, SerpApi, or
Open-Meteo calls are made.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ---------------------------------------------------------------------------
# In-memory SQLite database fixtures
# ---------------------------------------------------------------------------

# Import Base & models *before* creating the engine so that metadata is
# populated correctly.
from backend.app.database.database import Base  # noqa: E402
from backend.app.database.models import Trip  # noqa: E402  registers model
from backend.app.database.crud import save_trip, get_trip, get_all_trips  # noqa: E402
from backend.app.api.schemas import TripDetailResponse, TripSummary  # noqa: E402


SQLITE_URL = "sqlite://"  # pure in-memory, no file


@pytest.fixture()
def db_session():
    """Provide a fresh in-memory SQLite session for each test.

    SQLite does not support the PostgreSQL-specific JSONB type.  We patch
    each JSONB column to use the generic JSON type before calling create_all,
    then restore the originals so the production model is unchanged.
    """
    from sqlalchemy import JSON
    from sqlalchemy.dialects.postgresql import JSONB

    engine = create_engine(
        SQLITE_URL,
        connect_args={"check_same_thread": False},
    )

    # Collect columns that use JSONB and replace them temporarily.
    trip_table = Trip.__table__
    patched: list[tuple] = []  # (column, original_type)
    for col in trip_table.columns:
        if isinstance(col.type, JSONB):
            patched.append((col, col.type))
            col.type = JSON()

    try:
        Base.metadata.create_all(bind=engine)
        Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
        session = Session()
        try:
            yield session
        finally:
            session.close()
            Base.metadata.drop_all(bind=engine)
    finally:
        # Restore original JSONB types no matter what.
        for col, orig_type in patched:
            col.type = orig_type


# ---------------------------------------------------------------------------
# Helper: minimal valid state dict that mimics the LangGraph output
# ---------------------------------------------------------------------------

def _make_state(**overrides) -> dict:
    base = {
        "user_query": "Plan a 5-day trip from Delhi to Tokyo for 2 people.",
        "origin": "Delhi",
        "destination": "Tokyo",
        "start_date": "2026-10-10",
        "end_date": "2026-10-15",
        "trip_duration_days": 5,
        "travelers": 2,
        "budget": 150_000.0,
        "interests": ["anime", "food"],
        "itinerary": {
            "title": "Tokyo Adventure",
            "summary": "Five days in Tokyo.",
            "days": [{"day": 1, "title": "Arrival"}],
        },
        "estimated_cost": 120_000.0,
        "weather_data": {"trip_date_forecast_available": False},
        "flight_data": [{"price": 45_000, "airline": "Air India"}],
        "hotel_data": [{"name": "Hotel Gracery", "price_per_night": 5_000}],
        "attraction_data": [{"name": "Senso-ji", "category": "historic"}],
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# CRUD unit tests
# ---------------------------------------------------------------------------


def test_save_trip_persists_all_fields(db_session):
    """save_trip must write every research field to the database."""
    state = _make_state()
    trip = save_trip(db_session, state)

    assert trip.id is not None
    assert trip.user_query == state["user_query"]
    assert trip.origin == state["origin"]
    assert trip.destination == state["destination"]
    assert trip.start_date == state["start_date"]
    assert trip.end_date == state["end_date"]
    assert trip.trip_duration_days == state["trip_duration_days"]
    assert trip.travelers == state["travelers"]
    assert trip.budget == state["budget"]
    assert trip.interests == state["interests"]
    assert trip.itinerary == state["itinerary"]
    assert trip.estimated_cost == state["estimated_cost"]
    assert trip.weather_data == state["weather_data"]
    assert trip.flight_data == state["flight_data"]
    assert trip.hotel_data == state["hotel_data"]
    assert trip.attraction_data == state["attraction_data"]


def test_save_trip_without_optional_fields(db_session):
    """save_trip must succeed when optional research data is absent."""
    state = {
        "destination": "Paris",
    }
    trip = save_trip(db_session, state)
    assert trip.id is not None
    assert trip.destination == "Paris"
    assert trip.flight_data == []
    assert trip.hotel_data == []
    assert trip.attraction_data == []
    assert trip.weather_data == {}
    assert trip.interests == []


def test_get_trip_returns_none_for_missing_id(db_session):
    """get_trip must return None for a non-existent ID."""
    result = get_trip(db_session, 999)
    assert result is None


def test_get_all_trips_ordered_newest_first(db_session):
    """get_all_trips must return trips ordered by created_at descending."""
    state_a = _make_state(destination="Tokyo")
    state_b = _make_state(destination="Paris")
    trip_a = save_trip(db_session, state_a)
    trip_b = save_trip(db_session, state_b)

    trips = get_all_trips(db_session)
    # IDs increase monotonically, so the last saved has the highest id.
    assert trips[0].id == trip_b.id
    assert trips[1].id == trip_a.id


def test_get_trip_round_trips_full_data(db_session):
    """A saved trip fetched back must contain identical research data."""
    state = _make_state()
    saved = save_trip(db_session, state)
    fetched = get_trip(db_session, saved.id)

    assert fetched is not None
    assert fetched.flight_data == state["flight_data"]
    assert fetched.hotel_data == state["hotel_data"]
    assert fetched.attraction_data == state["attraction_data"]


# ---------------------------------------------------------------------------
# Schema tests
# ---------------------------------------------------------------------------


def test_trip_detail_response_schema_validates_full_payload():
    """TripDetailResponse must accept a complete trip payload."""
    payload = {
        "id": 1,
        "user_query": "A trip to Tokyo",
        "origin": "Delhi",
        "destination": "Tokyo",
        "start_date": "2026-10-10",
        "end_date": "2026-10-15",
        "trip_duration_days": 5,
        "travelers": 2,
        "budget": 150_000.0,
        "interests": ["anime"],
        "itinerary": {"title": "Tokyo", "days": []},
        "estimated_cost": 120_000.0,
        "weather_data": {},
        "flight_data": [{"price": 45_000}],
        "hotel_data": [{"name": "Hotel"}],
        "attraction_data": [{"name": "Temple"}],
        "created_at": datetime.now(timezone.utc),
    }
    detail = TripDetailResponse(**payload)
    assert detail.destination == "Tokyo"
    assert len(detail.flight_data) == 1
    assert len(detail.hotel_data) == 1
    assert len(detail.attraction_data) == 1


def test_trip_detail_response_schema_accepts_minimal_payload():
    """TripDetailResponse must accept a payload with only required fields."""
    payload = {
        "id": 2,
        "destination": "Paris",
        "created_at": datetime.now(timezone.utc),
    }
    detail = TripDetailResponse(**payload)
    assert detail.destination == "Paris"
    assert detail.flight_data == []
    assert detail.hotel_data == []
    assert detail.attraction_data == []
    assert detail.user_query is None
    assert detail.origin is None


def test_trip_summary_schema():
    """TripSummary must serialise the id and destination correctly."""
    summary = TripSummary(
        id=7,
        destination="Kyoto",
        created_at=datetime.now(timezone.utc),
    )
    assert summary.id == 7
    assert summary.destination == "Kyoto"
    assert summary.trip_duration_days is None


# ---------------------------------------------------------------------------
# FastAPI endpoint integration tests (mocked DB)
# ---------------------------------------------------------------------------


def _make_mock_trip(**overrides):
    """Return a MagicMock that looks like a persisted Trip ORM object."""
    m = MagicMock(spec=Trip)
    m.id = 1
    m.user_query = "Plan a trip to Tokyo"
    m.origin = "Delhi"
    m.destination = "Tokyo"
    m.start_date = "2026-10-10"
    m.end_date = "2026-10-15"
    m.trip_duration_days = 5
    m.travelers = 2
    m.budget = 150_000.0
    m.interests = ["anime", "food"]
    m.itinerary = {"title": "Tokyo Adventure", "days": []}
    m.estimated_cost = 120_000.0
    m.weather_data = {"trip_date_forecast_available": False}
    m.flight_data = [{"price": 45_000}]
    m.hotel_data = [{"name": "Hotel Gracery"}]
    m.attraction_data = [{"name": "Senso-ji"}]
    m.created_at = datetime(2026, 10, 1, 12, 0, 0)
    for k, v in overrides.items():
        setattr(m, k, v)
    return m


def test_fetch_trip_endpoint_returns_full_data():
    """GET /trips/{trip_id} must include flight_data, hotel_data, attraction_data."""
    from backend.app.main import app, get_db

    mock_trip = _make_mock_trip()

    def override_db():
        mock_db = MagicMock()
        yield mock_db

    app.dependency_overrides[get_db] = override_db

    with patch("backend.app.main.get_trip", return_value=mock_trip):
        client = TestClient(app)
        response = client.get("/trips/1")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["destination"] == "Tokyo"
    assert data["user_query"] == "Plan a trip to Tokyo"
    assert data["origin"] == "Delhi"
    assert len(data["flight_data"]) == 1
    assert len(data["hotel_data"]) == 1
    assert len(data["attraction_data"]) == 1


def test_fetch_trip_endpoint_returns_404_for_missing_trip():
    """GET /trips/{trip_id} must return 404 when the trip does not exist."""
    from backend.app.main import app, get_db

    def override_db():
        mock_db = MagicMock()
        yield mock_db

    app.dependency_overrides[get_db] = override_db

    with patch("backend.app.main.get_trip", return_value=None):
        client = TestClient(app)
        response = client.get("/trips/999")

    app.dependency_overrides.clear()

    assert response.status_code == 404


def test_fetch_trips_endpoint_returns_list():
    """GET /trips must return a count and list of trip summaries."""
    from backend.app.main import app, get_db

    mock_trips = [
        _make_mock_trip(id=1, destination="Tokyo"),
        _make_mock_trip(id=2, destination="Kyoto"),
    ]

    def override_db():
        mock_db = MagicMock()
        yield mock_db

    app.dependency_overrides[get_db] = override_db

    with patch("backend.app.main.get_all_trips", return_value=mock_trips):
        client = TestClient(app)
        response = client.get("/trips")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 2
    assert data["trips"][0]["destination"] == "Tokyo"


def test_fetch_trips_endpoint_empty_history():
    """GET /trips must return an empty list when no trips have been saved."""
    from backend.app.main import app, get_db

    def override_db():
        mock_db = MagicMock()
        yield mock_db

    app.dependency_overrides[get_db] = override_db

    with patch("backend.app.main.get_all_trips", return_value=[]):
        client = TestClient(app)
        response = client.get("/trips")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 0
    assert data["trips"] == []
