from datetime import date

import httpx


FORECAST_WINDOW_DAYS = 6


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None

    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def normalize_daily_forecast(forecast_data: dict | None) -> list[dict]:
    """Turn Open-Meteo columnar daily arrays into row objects for the UI."""

    if not forecast_data or not isinstance(forecast_data, dict):
        return []

    daily = forecast_data.get("daily")

    if isinstance(daily, list):
        return [
            item
            for item in daily
            if isinstance(item, dict)
        ]

    if not isinstance(daily, dict):
        return []

    times = daily.get("time") or []
    max_temps = daily.get("temperature_2m_max") or []
    min_temps = daily.get("temperature_2m_min") or []
    rain = daily.get("precipitation_probability_max") or []

    rows = []

    for index, day in enumerate(times):
        rows.append(
            {
                "date": day,
                "temperature_max": (
                    max_temps[index]
                    if index < len(max_temps)
                    else None
                ),
                "temperature_min": (
                    min_temps[index]
                    if index < len(min_temps)
                    else None
                ),
                "precipitation_probability": (
                    rain[index]
                    if index < len(rain)
                    else None
                ),
            }
        )

    return rows


def _in_forecast_window(
    trip_start: date | None,
    today: date | None = None,
) -> bool:
    if trip_start is None:
        return True

    today = today or date.today()
    delta = (trip_start - today).days

    return 0 <= delta <= FORECAST_WINDOW_DAYS


async def get_weather(
    latitude: float,
    longitude: float,
    start_date: str | None = None,
    end_date: str | None = None,
):
    """
    Get a short trip-date forecast from Open-Meteo.

    Open-Meteo provides a short forecast window. If the requested
    trip starts outside that window, no forecast request is made and
    the response clearly states that trip-date weather is unavailable.
    """

    trip_start = _parse_date(start_date)
    in_window = _in_forecast_window(trip_start)

    # Do NOT call Open-Meteo when the requested trip is outside
    # the supported forecast window.
    if not in_window:
        return {
            "trip_date_forecast_available": False,
            "requested_trip_start": start_date,
            "requested_trip_end": end_date,
            "forecast_window_days": FORECAST_WINDOW_DAYS + 1,
            "current": {},
            "daily": [],
            "warning": (
                "Trip dates are outside the available short forecast "
                "range; trip-date weather is unavailable."
            ),
        }

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": (
            "temperature_2m,"
            "precipitation,"
            "weather_code"
        ),
        "daily": (
            "temperature_2m_max,"
            "temperature_2m_min,"
            "precipitation_probability_max"
        ),
        "forecast_days": 7,
        "timezone": "auto",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                url,
                params=params,
            )
            response.raise_for_status()
            forecast_data = response.json()

    except httpx.HTTPError as e:
        return {
            "error": "Weather service unavailable",
            "details": str(e),
        }

    daily = normalize_daily_forecast(forecast_data)
    current = forecast_data.get("current") or {}

    return {
        "trip_date_forecast_available": True,
        "requested_trip_start": start_date,
        "requested_trip_end": end_date,
        "forecast_window_days": FORECAST_WINDOW_DAYS + 1,
        "current": current,
        "daily": daily,
        "forecast_data": forecast_data,
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
            response = await client.get(
                url,
                params=params,
            )
            response.raise_for_status()

            data = response.json()
            results = data.get("results", [])

            if not results:
                return {
                    "error": (
                        f"Could not find destination: {destination}"
                    )
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