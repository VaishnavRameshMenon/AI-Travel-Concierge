import os
from typing import Any, Dict, List, Optional

import httpx
from dotenv import load_dotenv

load_dotenv()

SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
SERPAPI_URL = "https://serpapi.com/search.json"


def _safe_float(value: Any) -> Optional[float]:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _parse_hotel(
    hotel: Dict[str, Any],
    travelers: int,
) -> Dict[str, Any]:
    nightly = hotel.get("rate_per_night", {})
    total = hotel.get("total_rate", {})

    return {
        "name": hotel.get("name"),
        "description": hotel.get("description"),
        "hotel_class": hotel.get("hotel_class"),
        "rating": _safe_float(hotel.get("overall_rating")),
        "reviews": hotel.get("reviews"),
        "price_per_night": _safe_float(
            nightly.get("extracted_lowest")
        ),
        "total_price": _safe_float(
            total.get("extracted_lowest")
        ),
        "currency": "INR",
        "travelers": travelers,
        "image": (
            hotel.get("images", [{}])[0].get("thumbnail")
            if hotel.get("images")
            else None
        ),
        "link": hotel.get("link"),
        "address": hotel.get("address"),
        "check_in_time": hotel.get("check_in_time"),
        "check_out_time": hotel.get("check_out_time"),
        "amenities": hotel.get("amenities", []),
        "source": "serpapi_google_hotels",
        "sponsored": hotel.get("sponsored", False),
    }


async def search_hotels(
    destination: str,
    check_in_date: Optional[str] = None,
    check_out_date: Optional[str] = None,
    travelers: int = 1,
    budget: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Search Google Hotels through SerpApi.

    Returns real hotel search results when available.
    Falls back safely with a warning instead of inventing hotels.
    """

    if not SERPAPI_API_KEY:
        return {
            "hotels": [],
            "source": "unavailable",
            "warning": "SERPAPI_API_KEY is not configured.",
        }

    if not destination:
        return {
            "hotels": [],
            "source": "unavailable",
            "warning": "A destination is required for hotel search.",
        }

    if not check_in_date or not check_out_date:
        return {
            "hotels": [],
            "source": "unavailable",
            "warning": "Check-in and check-out dates are required.",
        }

    params = {
        "engine": "google_hotels",
        "api_key": SERPAPI_API_KEY,
        "q": destination,
        "check_in_date": check_in_date,
        "check_out_date": check_out_date,
        "adults": max(1, travelers),
        "currency": "INR",
        "hl": "en",
        "gl": "in",
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                SERPAPI_URL,
                params=params,
            )

        if response.status_code != 200:
            return {
                "hotels": [],
                "source": "unavailable",
                "warning": (
                    f"SerpApi hotel search returned "
                    f"HTTP {response.status_code}."
                ),
            }

        data = response.json()

        if data.get("error"):
            return {
                "hotels": [],
                "source": "unavailable",
                "warning": f"SerpApi hotel search error: {data['error']}",
            }

        properties: List[Dict[str, Any]] = data.get(
            "properties",
            [],
        )

        hotels = []

        for hotel in properties[:10]:
            parsed = _parse_hotel(
                hotel,
                travelers,
            )

            # If a budget is provided, prefer hotels whose total
            # price is within that budget. We do not fabricate
            # or remove all results if none match.
            hotels.append(parsed)

        if budget is not None and hotels:
            within_budget = [
                hotel
                for hotel in hotels
                if (
                    hotel.get("total_price") is not None
                    and hotel["total_price"] <= budget
                )
            ]

            if within_budget:
                hotels = within_budget

        if not hotels:
            return {
                "hotels": [],
                "source": "serpapi_google_hotels",
                "warning": (
                    f"No Google Hotels results found for "
                    f"{destination}."
                ),
            }

        return {
            "hotels": hotels,
            "source": "serpapi_google_hotels",
            "live": True,
            "search_parameters": {
                "destination": destination,
                "check_in_date": check_in_date,
                "check_out_date": check_out_date,
                "travelers": travelers,
                "budget": budget,
                "currency": "INR",
            },
        }

    except httpx.TimeoutException:
        return {
            "hotels": [],
            "source": "unavailable",
            "warning": "Hotel search timed out.",
        }

    except httpx.RequestError as exc:
        return {
            "hotels": [],
            "source": "unavailable",
            "warning": f"Hotel search network error: {str(exc)}",
        }

    except Exception as exc:
        return {
            "hotels": [],
            "source": "unavailable",
            "warning": f"Unexpected hotel search error: {str(exc)}",
        }