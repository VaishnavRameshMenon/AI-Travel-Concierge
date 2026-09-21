import os
from typing import Any, Dict, List, Optional

import httpx
from dotenv import load_dotenv

load_dotenv()

SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")

SERPAPI_URL = "https://serpapi.com/search.json"


# Common city -> IATA airport mapping.
# This avoids depending on the old Aviationstack airport endpoint.
CITY_TO_IATA = {
    "delhi": "DEL",
    "new delhi": "DEL",
    "mumbai": "BOM",
    "bombay": "BOM",
    "bangalore": "BLR",
    "bengaluru": "BLR",
    "chennai": "MAA",
    "hyderabad": "HYD",
    "kolkata": "CCU",
    "calcutta": "CCU",
    "pune": "PNQ",
    "ahmedabad": "AMD",
    "kochi": "COK",
    "cochin": "COK",
    "goa": "GOI",
    "tokyo": "NRT",
    "narita": "NRT",
    "osaka": "KIX",
    "kyoto": "KIX",
    "seoul": "ICN",
    "singapore": "SIN",
    "bangkok": "BKK",
    "dubai": "DXB",
    "london": "LHR",
    "paris": "CDG",
    "frankfurt": "FRA",
    "new york": "JFK",
    "los angeles": "LAX",
    "san francisco": "SFO",
    "toronto": "YYZ",
    "sydney": "SYD",
    "melbourne": "MEL",
}


def find_airport_iata(city: str) -> Optional[str]:
    """
    Resolve a city name to a common IATA airport code.
    """
    if not city:
        return None

    city_clean = city.strip().lower()

    # Direct IATA code support
    if len(city_clean) == 3 and city_clean.isalpha():
        return city_clean.upper()

    return CITY_TO_IATA.get(city_clean)


def _parse_flight_option(
    option: Dict[str, Any],
    travelers: int,
) -> Dict[str, Any]:
    """
    Convert a SerpApi Google Flights result into the project's
    simpler internal flight representation.
    """

    segments = option.get("flights", [])

    parsed_segments = []

    for segment in segments:
        departure = segment.get("departure_airport", {})
        arrival = segment.get("arrival_airport", {})

        parsed_segments.append(
            {
                "airline": segment.get("airline"),
                "airline_logo": segment.get("airline_logo"),
                "flight_number": segment.get("flight_number"),
                "departure_airport": departure.get("id"),
                "departure_airport_name": departure.get("name"),
                "departure_time": departure.get("time"),
                "arrival_airport": arrival.get("id"),
                "arrival_airport_name": arrival.get("name"),
                "arrival_time": arrival.get("time"),
                "duration_minutes": segment.get("duration"),
                "travel_class": segment.get("travel_class"),
                "airplane": segment.get("airplane"),
            }
        )

    price = option.get("price")

    try:
        price = float(price) if price is not None else None
    except (TypeError, ValueError):
        price = None

    return {
        "price": price,
        "currency": "INR",
        "travelers": travelers,
        "total_duration_minutes": option.get("total_duration"),
        "number_of_stops": option.get("layovers", []).__len__(),
        "segments": parsed_segments,
        "source": "serpapi_google_flights",
    }


async def search_flights(
    origin: str,
    destination: str,
    departure_date: Optional[str] = None,
    return_date: Optional[str] = None,
    travelers: int = 1,
) -> Dict[str, Any]:
    """
    Search Google Flights through SerpApi.

    Returns real search results when the SerpApi key and required
    route/date information are available.

    Falls back safely with a warning instead of inventing flight data.
    """

    if not SERPAPI_API_KEY:
        return {
            "flights": [],
            "source": "unavailable",
            "warning": "SERPAPI_API_KEY is not configured.",
        }

    origin_iata = find_airport_iata(origin)
    destination_iata = find_airport_iata(destination)

    if not origin_iata:
        return {
            "flights": [],
            "source": "unavailable",
            "warning": f"Could not resolve departure airport for '{origin}'.",
        }

    if not destination_iata:
        return {
            "flights": [],
            "source": "unavailable",
            "warning": f"Could not resolve arrival airport for '{destination}'.",
        }

    if not departure_date:
        return {
            "flights": [],
            "source": "unavailable",
            "warning": "A departure date is required for flight search.",
        }

    # We use round-trip search when a return date is available.
    # Otherwise use one-way search.
    flight_type = "1" if return_date else "2"

    params = {
        "engine": "google_flights",
        "api_key": SERPAPI_API_KEY,
        "departure_id": origin_iata,
        "arrival_id": destination_iata,
        "outbound_date": departure_date,
        "type": flight_type,
        "adults": max(1, travelers),
        "currency": "INR",
        "hl": "en",
        "gl": "in",
        "travel_class": "1",
        "sort_by": "1",
    }

    if return_date:
        params["return_date"] = return_date

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                SERPAPI_URL,
                params=params,
            )

        if response.status_code != 200:
            return {
                "flights": [],
                "source": "unavailable",
                "warning": (
                    f"SerpApi flight search returned "
                    f"HTTP {response.status_code}."
                ),
            }

        data = response.json()

        if data.get("error"):
            return {
                "flights": [],
                "source": "unavailable",
                "warning": f"SerpApi flight search error: {data['error']}",
            }

        flight_options: List[Dict[str, Any]] = []

        # SerpApi returns the strongest options in best_flights
        # and additional options in other_flights.
        raw_options = []

        raw_options.extend(data.get("best_flights", []))
        raw_options.extend(data.get("other_flights", []))

        for option in raw_options[:10]:
            parsed = _parse_flight_option(
                option,
                travelers,
            )

            flight_options.append(parsed)

        if not flight_options:
            return {
                "flights": [],
                "source": "serpapi_google_flights",
                "warning": (
                    f"No Google Flights results found for "
                    f"{origin_iata} → {destination_iata} "
                    f"on {departure_date}."
                ),
            }

        return {
            "flights": flight_options,
            "source": "serpapi_google_flights",
            "live": True,
            "search_parameters": {
                "origin": origin,
                "destination": destination,
                "origin_iata": origin_iata,
                "destination_iata": destination_iata,
                "departure_date": departure_date,
                "return_date": return_date,
                "travelers": travelers,
                "currency": "INR",
            },
            "google_flights_link": data.get("search_metadata", {}).get(
                "google_flights_url"
            ),
        }

    except httpx.TimeoutException:
        return {
            "flights": [],
            "source": "unavailable",
            "warning": "Flight search timed out.",
        }

    except httpx.RequestError as exc:
        return {
            "flights": [],
            "source": "unavailable",
            "warning": f"Flight search network error: {str(exc)}",
        }

    except Exception as exc:
        return {
            "flights": [],
            "source": "unavailable",
            "warning": f"Unexpected flight search error: {str(exc)}",
        }