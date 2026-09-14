import os

import httpx
from dotenv import load_dotenv


load_dotenv()


AVIATIONSTACK_API_KEY = os.getenv(
    "AVIATIONSTACK_API_KEY"
)

BASE_URL = "https://api.aviationstack.com/v1"


# ============================================================
# COMMON CITY -> IATA MAPPING
# ============================================================

CITY_IATA = {
    "delhi": "DEL",
    "new delhi": "DEL",

    "mumbai": "BOM",
    "bombay": "BOM",

    "bangalore": "BLR",
    "bengaluru": "BLR",

    "chennai": "MAA",
    "madras": "MAA",

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


# ============================================================
# AIRPORT LOOKUP
# ============================================================

async def find_airport_iata(
    location: str,
):
    """
    Resolve a city/location to a commonly used IATA code.

    A local mapping is used instead of making an additional
    Aviationstack airport API request. This avoids unnecessary
    API quota usage and keeps flight search reliable.
    """

    if not location:
        return {
            "success": False,
            "error": "Airport location is required.",
        }

    normalized = location.strip().lower()

    # Direct city lookup
    iata = CITY_IATA.get(normalized)

    if iata:
        return {
            "success": True,
            "iata": iata,
            "location": location,
            "source": "local_iata_mapping",
        }

    # Try partial matching
    for city, code in CITY_IATA.items():

        if city in normalized or normalized in city:
            return {
                "success": True,
                "iata": code,
                "location": location,
                "source": "local_iata_mapping",
            }

    return {
        "success": False,
        "error": (
            f"No IATA code is configured for "
            f"'{location}'."
        ),
    }


# ============================================================
# FLIGHT SEARCH
# ============================================================

async def search_flights(
    departure_iata: str,
    arrival_iata: str,
    flight_date: str | None = None,
):
    """
    Search flights using Aviationstack.
    """

    if not AVIATIONSTACK_API_KEY:
        return {
            "success": False,
            "error": (
                "Aviationstack API key is not configured."
            ),
            "flights": [],
        }

    if not departure_iata or not arrival_iata:
        return {
            "success": False,
            "error": (
                "Departure and arrival airport "
                "codes are required."
            ),
            "flights": [],
        }

    url = f"{BASE_URL}/flights"

    params = {
        "access_key": AVIATIONSTACK_API_KEY,
        "dep_iata": departure_iata,
        "arr_iata": arrival_iata,
        "limit": 10,
    }

    if flight_date:
        params["flight_date"] = flight_date

    try:
        async with httpx.AsyncClient(
            timeout=15.0
        ) as client:

            response = await client.get(
                url,
                params=params,
            )

            response.raise_for_status()

            data = response.json()

            if data.get("error"):
                return {
                    "success": False,
                    "error": data["error"],
                    "flights": [],
                }

            flights = []

            for flight in data.get(
                "data",
                [],
            ):

                flights.append(
                    {
                        "flight_number": (
                            flight.get(
                                "flight",
                                {},
                            ).get("iata")
                            or flight.get(
                                "flight",
                                {},
                            ).get("number")
                        ),

                        "airline": (
                            flight.get(
                                "airline",
                                {},
                            ).get("name")
                        ),

                        "departure": (
                            flight.get(
                                "departure",
                                {},
                            ).get("airport")
                        ),

                        "departure_iata": (
                            flight.get(
                                "departure",
                                {},
                            ).get("iata")
                        ),

                        "arrival": (
                            flight.get(
                                "arrival",
                                {},
                            ).get("airport")
                        ),

                        "arrival_iata": (
                            flight.get(
                                "arrival",
                                {},
                            ).get("iata")
                        ),

                        "departure_time": (
                            flight.get(
                                "departure",
                                {},
                            ).get("scheduled")
                        ),

                        "arrival_time": (
                            flight.get(
                                "arrival",
                                {},
                            ).get("scheduled")
                        ),

                        "status": flight.get(
                            "flight_status"
                        ),
                    }
                )

            return {
                "success": True,
                "provider": "aviationstack",
                "flights": flights,
            }

    except httpx.HTTPStatusError as e:

        return {
            "success": False,
            "error": (
                f"Flight API returned "
                f"HTTP {e.response.status_code}."
            ),
            "flights": [],
        }

    except httpx.HTTPError as e:

        return {
            "success": False,
            "error": "Flight service unavailable.",
            "details": str(e),
            "flights": [],
        }

    except Exception as e:

        return {
            "success": False,
            "error": (
                "Unexpected flight service error."
            ),
            "details": str(e),
            "flights": [],
        }