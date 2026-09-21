import asyncio
from datetime import date, timedelta

from backend.app.tools.attractions import search_attractions
from backend.app.tools.flights import find_airport_iata
from backend.app.tools.hotels import search_hotels
from backend.app.tools.weather import get_weather


def test_attractions_falls_back_without_provider_key(monkeypatch):
    monkeypatch.setattr("backend.app.tools.attractions.OPENTRIPMAP_API_KEY", None)
    result = asyncio.run(search_attractions(35.7, 139.75, ["anime", "food"]))
    assert result["success"] is True
    assert result["provider"] == "fallback"
    assert any(place["category"] == "anime" for place in result["attractions"])


def test_hotel_options_are_explicitly_fallback_data():
    result = asyncio.run(search_hotels("Tokyo"))
    assert result["success"] is True
    assert all(hotel["source"] == "fallback" for hotel in result["hotels"])


def test_known_city_resolves_to_iata():
    result = asyncio.run(find_airport_iata("Delhi"))
    assert result == {"success": True, "iata": "DEL", "location": "Delhi", "source": "local_iata_mapping"}


def test_future_trip_weather_is_marked_unavailable_without_http(monkeypatch):
    class Client:
        def __init__(self, *args, **kwargs):
            raise AssertionError("Open-Meteo must not be called for an out-of-range trip")
    monkeypatch.setattr("backend.app.tools.weather.httpx.AsyncClient", Client)
    start = (date.today() + timedelta(days=30)).isoformat()
    result = asyncio.run(get_weather(35.7, 139.75, start, start))
    assert result["trip_date_forecast_available"] is False
    assert result["warning"]
