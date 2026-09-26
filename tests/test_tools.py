import asyncio
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.app.tools.attractions import fallback_attractions, search_attractions
from backend.app.tools.flights import CITY_TO_IATA, find_airport_iata, search_flights
from backend.app.tools.hotels import search_hotels
from backend.app.tools.weather import geocode_destination, get_weather


# ============================================================
# FLIGHT TOOL TESTS
# ============================================================


def test_find_airport_iata_resolves_known_cities():
    """Verify synchronous resolution of city names to airport IATA codes."""
    assert find_airport_iata("Delhi") == "DEL"
    assert find_airport_iata("new delhi") == "DEL"
    assert find_airport_iata("tokyo") == "NRT"
    assert find_airport_iata("Bangalore") == "BLR"
    assert find_airport_iata("bengaluru") == "BLR"
    assert find_airport_iata("London") == "LHR"
    assert find_airport_iata("Paris") == "CDG"


def test_find_airport_iata_handles_raw_codes_and_unknowns():
    """Verify direct IATA codes pass through and unknown cities return None."""
    assert find_airport_iata("JFK") == "JFK"
    assert find_airport_iata("dxb") == "DXB"
    assert find_airport_iata("Unknown City Nowhere") is None
    assert find_airport_iata("") is None
    assert find_airport_iata("   ") is None


def test_flight_search_requires_departure_date():
    """Flight search must return an unavailable status when departure date is missing."""
    result = asyncio.run(
        search_flights(
            origin="Delhi",
            destination="Tokyo",
            departure_date=None,
        )
    )
    assert result["source"] == "unavailable"
    assert result["flights"] == []
    assert "departure date" in result["warning"].lower()


def test_flight_search_fails_gracefully_on_unresolvable_city():
    """Flight search must fail gracefully when origin or destination city cannot be resolved."""
    result = asyncio.run(
        search_flights(
            origin="Atlantis Island",
            destination="Tokyo",
            departure_date="2026-10-10",
        )
    )
    assert result["source"] == "unavailable"
    assert result["flights"] == []
    assert "departure airport" in result["warning"].lower()


def test_flight_search_fails_gracefully_without_api_key(monkeypatch):
    """Flight search returns unavailable status when SerpApi key is missing."""
    monkeypatch.setattr("backend.app.tools.flights.SERPAPI_API_KEY", None)
    result = asyncio.run(
        search_flights(
            origin="Delhi",
            destination="Tokyo",
            departure_date="2026-10-10",
        )
    )
    assert result["source"] == "unavailable"
    assert "SERPAPI_API_KEY is not configured" in result["warning"]


def test_flight_search_parses_mocked_serpapi_response(monkeypatch):
    """Verify parsing of Google Flights results from mocked SerpApi response."""
    monkeypatch.setattr("backend.app.tools.flights.SERPAPI_API_KEY", "test_mock_key")

    mock_response_data = {
        "best_flights": [
            {
                "price": 45000,
                "total_duration": 480,
                "layovers": [],
                "flights": [
                    {
                        "airline": "Air India",
                        "airline_logo": "https://example.com/ai.png",
                        "flight_number": "AI 306",
                        "departure_airport": {"id": "DEL", "name": "Indira Gandhi International", "time": "2026-10-10 21:15"},
                        "arrival_airport": {"id": "NRT", "name": "Narita International", "time": "2026-10-11 08:45"},
                        "duration": 480,
                        "travel_class": "Economy",
                        "airplane": "Boeing 787",
                    }
                ],
            }
        ],
        "other_flights": [],
        "search_metadata": {"google_flights_url": "https://google.com/flights/test"},
    }

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_response_data

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None

    with patch("backend.app.tools.flights.httpx.AsyncClient", return_value=mock_client):
        result = asyncio.run(
            search_flights(
                origin="Delhi",
                destination="Tokyo",
                departure_date="2026-10-10",
                return_date="2026-10-16",
                travelers=2,
            )
        )

    assert result["live"] is True
    assert result["source"] == "serpapi_google_flights"
    assert len(result["flights"]) == 1
    parsed_flight = result["flights"][0]
    assert parsed_flight["price"] == 45000.0
    assert parsed_flight["number_of_stops"] == 0
    assert parsed_flight["total_duration_minutes"] == 480
    assert parsed_flight["segments"][0]["airline"] == "Air India"
    assert parsed_flight["segments"][0]["departure_airport"] == "DEL"
    assert parsed_flight["segments"][0]["arrival_airport"] == "NRT"


# ============================================================
# HOTEL TOOL TESTS
# ============================================================


def test_hotel_search_requires_dates():
    """Hotel search must return unavailable status when check-in or check-out dates are missing."""
    result = asyncio.run(search_hotels("Tokyo"))
    assert result["source"] == "unavailable"
    assert result["hotels"] == []
    assert "check-in and check-out dates are required" in result["warning"].lower()


def test_hotel_search_fails_gracefully_without_api_key(monkeypatch):
    """Hotel search returns unavailable status when SerpApi key is missing."""
    monkeypatch.setattr("backend.app.tools.hotels.SERPAPI_API_KEY", None)
    result = asyncio.run(
        search_hotels(
            destination="Tokyo",
            check_in_date="2026-10-10",
            check_out_date="2026-10-16",
        )
    )
    assert result["source"] == "unavailable"
    assert "SERPAPI_API_KEY is not configured" in result["warning"]


def test_hotel_search_parses_mocked_serpapi_response(monkeypatch):
    """Verify parsing and budget filtering of Google Hotels from mocked SerpApi response."""
    monkeypatch.setattr("backend.app.tools.hotels.SERPAPI_API_KEY", "test_mock_key")

    mock_response_data = {
        "properties": [
            {
                "name": "Hotel Gracery Shinjuku",
                "description": "Upscale Godzilla-themed hotel in Shinjuku",
                "hotel_class": "4-star",
                "overall_rating": 4.5,
                "reviews": 3200,
                "rate_per_night": {"extracted_lowest": 8500},
                "total_rate": {"extracted_lowest": 51000},
                "amenities": ["Free Wi-Fi", "Restaurant", "Air conditioning"],
                "images": [{"thumbnail": "https://example.com/hotel.jpg"}],
                "link": "https://example.com/property",
            },
            {
                "name": "Luxury Palace Tokyo",
                "overall_rating": 4.9,
                "rate_per_night": {"extracted_lowest": 40000},
                "total_rate": {"extracted_lowest": 240000},
                "amenities": ["Spa", "Pool"],
            },
        ]
    }

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_response_data

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None

    with patch("backend.app.tools.hotels.httpx.AsyncClient", return_value=mock_client):
        # Query with budget constraint: 60,000 INR
        result = asyncio.run(
            search_hotels(
                destination="Tokyo",
                check_in_date="2026-10-10",
                check_out_date="2026-10-16",
                travelers=2,
                budget=60000,
            )
        )

    assert result["live"] is True
    assert result["source"] == "serpapi_google_hotels"
    # The luxury hotel (240,000) should be filtered out by the 60,000 budget
    assert len(result["hotels"]) == 1
    hotel = result["hotels"][0]
    assert hotel["name"] == "Hotel Gracery Shinjuku"
    assert hotel["rating"] == 4.5
    assert hotel["price_per_night"] == 8500.0
    assert hotel["total_price"] == 51000.0
    assert "Free Wi-Fi" in hotel["amenities"]


# ============================================================
# ATTRACTION TOOL TESTS
# ============================================================


def test_attractions_falls_back_without_provider_key(monkeypatch):
    """Verify interest-based fallback when OpenTripMap key is absent."""
    monkeypatch.setattr("backend.app.tools.attractions.OPENTRIPMAP_API_KEY", None)
    result = asyncio.run(search_attractions(35.7, 139.75, ["anime", "food"]))
    assert result["success"] is True
    assert result["provider"] == "fallback"
    categories = [place["category"] for place in result["attractions"]]
    assert "anime" in categories
    assert "food" in categories


def test_attractions_handles_missing_coordinates():
    """Verify graceful handling when destination coordinates are missing."""
    result = asyncio.run(search_attractions(latitude=None, longitude=None, interests=["photography"]))
    assert result["success"] is False
    assert result["provider"] == "fallback"
    assert "coordinates are required" in result["error"].lower()
    assert len(result["attractions"]) > 0


def test_attractions_parses_mocked_opentripmap_response(monkeypatch):
    """Verify live OpenTripMap response parsing with mock client."""
    monkeypatch.setattr("backend.app.tools.attractions.OPENTRIPMAP_API_KEY", "mock_key")

    mock_places = [
        {
            "name": "Senso-ji",
            "kinds": "historic,cultural",
            "point": {"lat": 35.7147, "lon": 139.7967},
            "xid": "N12345",
        }
    ]

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_places

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None

    with patch("backend.app.tools.attractions.httpx.AsyncClient", return_value=mock_client):
        result = asyncio.run(search_attractions(35.71, 139.79, ["history"]))

    assert result["success"] is True
    assert result["provider"] == "opentripmap"
    assert len(result["attractions"]) == 1
    assert result["attractions"][0]["name"] == "Senso-ji"


# ============================================================
# WEATHER & GEOCODING TESTS
# ============================================================


def test_future_trip_weather_is_marked_unavailable_without_http(monkeypatch):
    """Trips beyond the 7-day forecast window must not trigger network requests."""
    class FailClient:
        def __init__(self, *args, **kwargs):
            raise AssertionError("Open-Meteo must not be called for an out-of-range trip")

    monkeypatch.setattr("backend.app.tools.weather.httpx.AsyncClient", FailClient)
    start = (date.today() + timedelta(days=30)).isoformat()
    result = asyncio.run(get_weather(35.7, 139.75, start, start))
    assert result["trip_date_forecast_available"] is False
    assert result["warning"]


def test_weather_parses_mocked_open_meteo_response():
    """Verify in-range trip weather forecast parsing from mocked response."""
    start = date.today().isoformat()
    mock_forecast = {
        "current": {"temperature_2m": 22.5, "precipitation": 0.0},
        "daily": {"temperature_2m_max": [25.0], "temperature_2m_min": [18.0]},
    }

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_forecast

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None

    with patch("backend.app.tools.weather.httpx.AsyncClient", return_value=mock_client):
        result = asyncio.run(get_weather(35.68, 139.69, start, start))

    assert result["trip_date_forecast_available"] is True
    assert result["forecast_data"]["current"]["temperature_2m"] == 22.5


def test_geocode_destination_parses_mocked_results():
    """Verify geocoding coordinates parsing with mock client."""
    mock_geo = {
        "results": [
            {
                "name": "Tokyo",
                "country": "Japan",
                "latitude": 35.6895,
                "longitude": 139.6917,
                "timezone": "Asia/Tokyo",
            }
        ]
    }

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_geo

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None

    with patch("backend.app.tools.weather.httpx.AsyncClient", return_value=mock_client):
        result = asyncio.run(geocode_destination("Tokyo"))

    assert result["name"] == "Tokyo"
    assert result["country"] == "Japan"
    assert result["latitude"] == 35.6895
    assert result["longitude"] == 139.6917
