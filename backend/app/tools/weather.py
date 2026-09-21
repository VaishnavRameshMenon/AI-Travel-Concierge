from datetime import date
import httpx


async def get_weather(latitude: float, longitude: float, start_date: str | None = None, end_date: str | None = None):
    """
    Get current weather and a short forecast from Open-Meteo.
    """

    trip_start = date.fromisoformat(start_date) if start_date else None
    if trip_start and not 0 <= (trip_start - date.today()).days <= 6:
        return {"trip_date_forecast_available": False, "requested_trip_start": start_date, "requested_trip_end": end_date, "warning": "Trip dates are outside the available short forecast range; current conditions are not trip-date weather."}

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,precipitation,weather_code",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max",
        "forecast_days": 7,
        "timezone": "auto",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()

            return {"trip_date_forecast_available": True, "requested_trip_start": start_date, "requested_trip_end": end_date, "forecast_data": response.json()}

    except httpx.HTTPError as e:
        return {
            "error": "Weather service unavailable",
            "details": str(e),
        }

async def geocode_destination(destination: str):
    """
    Convert a destination name into latitude and longitude
    using Open-Meteo's geocoding service.
    """

    url = "https://geocoding-api.open-meteo.com/v1/search"

    params = {
        "name": destination,
        "count": 1,
        "language": "en",
        "format": "json",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()

            data = response.json()

            results = data.get("results", [])

            if not results:
                return {
                    "error": f"Could not find destination: {destination}"
                }

            location = results[0]

            return {
                "name": location.get("name"),
                "country": location.get("country"),
                "latitude": location.get("latitude"),
                "longitude": location.get("longitude"),
                "timezone": location.get("timezone"),
            }

    except httpx.HTTPError as e:
        return {
            "error": "Geocoding service unavailable",
            "details": str(e),
        }
