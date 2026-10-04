import os
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus

import httpx
from dotenv import load_dotenv

load_dotenv()

SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
SERPAPI_URL = "https://serpapi.com/search.json"

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
    "haneda": "HND",
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
    if not city:
        return None

    value = city.strip().lower()

    if len(value) == 3 and value.isalpha():
        return value.upper()

    if value in CITY_TO_IATA:
        return CITY_TO_IATA[value]

    for name, code in CITY_TO_IATA.items():
        if name in value:
            return code

    return None


def build_google_flights_search_url(
    origin_iata: str,
    destination_iata: str,
    departure_date: str,
    return_date: Optional[str],
    travelers: int,
) -> str:
    query = f"Flights from {origin_iata} to {destination_iata} on {departure_date}"
    if return_date:
        query += f" returning {return_date}"
    if travelers > 1:
        query += f" {travelers} passengers"

    return (
        "https://www.google.com/travel/flights?"
        f"q={quote_plus(query)}&hl=en&gl=in&curr=INR"
    )


def _number(value: Any) -> Optional[float]:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _parse_segment(segment: Dict[str, Any]) -> Dict[str, Any]:
    departure = segment.get("departure_airport") or segment.get("departure") or {}
    arrival = segment.get("arrival_airport") or segment.get("arrival") or {}

    departure_code = (
        departure.get("id")
        or departure.get("airport_code")
        or departure.get("code")
    )
    arrival_code = (
        arrival.get("id")
        or arrival.get("airport_code")
        or arrival.get("code")
    )

    return {
        "airline": segment.get("airline"),
        "airline_logo": segment.get("airline_logo"),
        "flight_number": segment.get("flight_number"),
        "departure_airport": departure_code,
        "departure_airport_name": departure.get("name"),
        "departure_time": departure.get("time"),
        "arrival_airport": arrival_code,
        "arrival_airport_name": arrival.get("name"),
        "arrival_time": arrival.get("time"),
        "duration_minutes": segment.get("duration"),
        "travel_class": segment.get("travel_class"),
        "airplane": segment.get("airplane"),
    }


def _parse_flight_option(
    option: Dict[str, Any],
    travelers: int,
    origin_iata: str,
    destination_iata: str,
    departure_date: str,
    return_date: Optional[str],
) -> Dict[str, Any]:
    raw_segments = option.get("flights") or []
    segments = [
        _parse_segment(segment)
        for segment in raw_segments
        if isinstance(segment, dict)
    ]

    total_duration = _number(option.get("total_duration"))
    if total_duration is None:
        segment_durations = [
            _number(segment.get("duration_minutes"))
            for segment in segments
            if _number(segment.get("duration_minutes")) is not None
        ]
        total_duration = sum(segment_durations) if segment_durations else None

    layovers = option.get("layovers") or []
    stops = len(layovers)
    if not layovers and len(segments) > 1:
        stops = len(segments) - 1

    price = _number(option.get("price"))
    search_url = build_google_flights_search_url(
        origin_iata,
        destination_iata,
        departure_date,
        return_date,
        travelers,
    )

    first = segments[0] if segments else {}
    last = segments[-1] if segments else {}

    return {
        # SerpApi's Google Flights `price` is the ticket price returned
        # for the passenger count requested through `adults`.
        "price": price,
        "currency": "INR",
        "travelers": travelers,
        "total_price": price,
        "price_per_traveler": (
            round(price / travelers, 2)
            if price is not None and travelers > 0
            else None
        ),
        "total_duration_minutes": int(total_duration) if total_duration is not None else None,
        "number_of_stops": stops,
        "stop_label": "Nonstop" if stops == 0 else f"{stops} stop" + ("s" if stops > 1 else ""),
        "segments": segments,
        "origin": first.get("departure_airport") or origin_iata,
        "destination": last.get("arrival_airport") or destination_iata,
        "airline": first.get("airline"),
        "departure_airport": first.get("departure_airport") or origin_iata,
        "arrival_airport": last.get("arrival_airport") or destination_iata,
        "departure_time": first.get("departure_time"),
        "arrival_time": last.get("arrival_time"),
        "search_url": search_url,
        "source": "serpapi_google_flights",
    }


async def search_flights(
    origin: str,
    destination: str,
    departure_date: Optional[str] = None,
    return_date: Optional[str] = None,
    travelers: int = 1,
) -> Dict[str, Any]:
    """Search Google Flights through SerpApi and return normalized results."""

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

    travelers = max(1, int(travelers or 1))

    params: Dict[str, Any] = {
        "engine": "google_flights",
        "api_key": SERPAPI_API_KEY,
        "departure_id": origin_iata,
        "arrival_id": destination_iata,
        "outbound_date": departure_date,
        "type": "1" if return_date else "2",
        "adults": travelers,
        "currency": "INR",
        "hl": "en",
        "gl": "in",
        "travel_class": "1",
        "sort_by": "2",
    }

    if return_date:
        params["return_date"] = return_date

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(SERPAPI_URL, params=params)

        if response.status_code != 200:
            return {
                "flights": [],
                "source": "unavailable",
                "warning": f"SerpApi flight search returned HTTP {response.status_code}.",
            }

        data = response.json()

        if data.get("error"):
            return {
                "flights": [],
                "source": "unavailable",
                "warning": f"SerpApi flight search error: {data['error']}",
            }

        raw_options: List[Dict[str, Any]] = []
        raw_options.extend(data.get("best_flights") or [])
        raw_options.extend(data.get("other_flights") or [])

        flights = [
            _parse_flight_option(
                option,
                travelers,
                origin_iata,
                destination_iata,
                departure_date,
                return_date,
            )
            for option in raw_options[:10]
            if isinstance(option, dict)
        ]

        if not flights:
            return {
                "flights": [],
                "source": "serpapi_google_flights",
                "warning": (
                    f"No Google Flights results found for "
                    f"{origin_iata} → {destination_iata} on {departure_date}."
                ),
            }

        flights.sort(
            key=lambda item: (
                item.get("price") is None,
                item.get("price") if item.get("price") is not None else float("inf"),
            )
        )

        search_url = build_google_flights_search_url(
            origin_iata,
            destination_iata,
            departure_date,
            return_date,
            travelers,
        )

        return {
            "flights": flights,
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
            "google_flights_link": search_url,
            "price_insights": data.get("price_insights") or {},
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
