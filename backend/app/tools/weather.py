import httpx


async def get_weather(latitude: float, longitude: float):
    """
    Get current weather and a short forecast from Open-Meteo.
    """

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

            return response.json()

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