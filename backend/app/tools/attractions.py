import os
from typing import List, Dict, Any

import httpx
from dotenv import load_dotenv


load_dotenv()


OPENTRIPMAP_API_KEY = os.getenv(
    "OPENTRIPMAP_API_KEY"
)

OPENTRIPMAP_BASE_URL = (
    "https://api.opentripmap.com/0.1"
)


# ============================================================
# FALLBACK DATA
# ============================================================

def fallback_attractions(
    interests: List[str] | None = None,
) -> List[Dict[str, Any]]:

    interests = interests or []

    attractions = []

    if any(
        interest.lower() in {
            "anime",
            "manga",
            "gaming",
            "otaku",
        }
        for interest in interests
    ):
        attractions.append(
            {
                "name": "Anime and pop-culture districts",
                "category": "anime",
                "source": "fallback",
            }
        )

    if any(
        interest.lower() in {
            "food",
            "cuisine",
            "restaurants",
            "street food",
        }
        for interest in interests
    ):
        attractions.append(
            {
                "name": "Local food districts and markets",
                "category": "food",
                "source": "fallback",
            }
        )

    if any(
        interest.lower() in {
            "photography",
            "photo",
            "nature",
            "scenery",
        }
        for interest in interests
    ):
        attractions.append(
            {
                "name": "Scenic photography locations",
                "category": "photography",
                "source": "fallback",
            }
        )

    attractions.extend(
        [
            {
                "name": "Local cultural attractions",
                "category": "culture",
                "source": "fallback",
            },
            {
                "name": "Popular city landmarks",
                "category": "landmark",
                "source": "fallback",
            },
        ]
    )

    return attractions


# ============================================================
# OPENTRIPMAP SEARCH
# ============================================================

async def search_opentripmap(
    latitude: float,
    longitude: float,
    radius: int = 5000,
    limit: int = 20,
) -> Dict[str, Any]:

    if not OPENTRIPMAP_API_KEY:
        return {
            "success": False,
            "error": (
                "OpenTripMap API key is not configured."
            ),
        }

    url = (
        f"{OPENTRIPMAP_BASE_URL}"
        "/places/radius"
    )

    params = {
        "apikey": OPENTRIPMAP_API_KEY,
        "radius": radius,
        "lon": longitude,
        "lat": latitude,
        "rate": 2,
        "format": "json",
        "limit": limit,
    }

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

            if isinstance(data, dict) and data.get("error"):
                return {
                    "success": False,
                    "error": data.get("error"),
                }

            places = []

            for place in data:

                if not isinstance(place, dict):
                    continue

                xid = place.get("xid")

                places.append(
                    {
                        "name": place.get(
                            "name",
                            "Unnamed attraction",
                        ),
                        "category": place.get(
                            "kinds"
                        ),
                        "latitude": (
                            place.get(
                                "point",
                                {}
                            ).get("lat")
                        ),
                        "longitude": (
                            place.get(
                                "point",
                                {}
                            ).get("lon")
                        ),
                        "xid": xid,
                        "source": "opentripmap",
                    }
                )

            return {
                "success": True,
                "provider": "opentripmap",
                "attractions": places,
            }

    except httpx.HTTPStatusError as e:

        return {
            "success": False,
            "error": (
                "OpenTripMap returned HTTP "
                f"{e.response.status_code}."
            ),
        }

    except httpx.HTTPError as e:

        return {
            "success": False,
            "error": (
                "OpenTripMap service unavailable."
            ),
            "details": str(e),
        }

    except Exception as e:

        return {
            "success": False,
            "error": (
                "Unexpected OpenTripMap error."
            ),
            "details": str(e),
        }


# ============================================================
# PUBLIC ATTRACTION SEARCH
# ============================================================

async def search_attractions(
    latitude: float,
    longitude: float,
    interests: List[str] | None = None,
) -> Dict[str, Any]:

    if latitude is None or longitude is None:

        return {
            "success": False,
            "provider": "fallback",
            "error": (
                "Destination coordinates are required."
            ),
            "attractions": fallback_attractions(
                interests
            ),
        }

    # --------------------------------------------------------
    # Try live provider
    # --------------------------------------------------------

    live_result = await search_opentripmap(
        latitude=latitude,
        longitude=longitude,
    )

    if (
        live_result.get("success")
        and live_result.get("attractions")
    ):

        return live_result

    # --------------------------------------------------------
    # Controlled fallback
    # --------------------------------------------------------

    return {
        "success": True,
        "provider": "fallback",
        "attractions": fallback_attractions(
            interests
        ),
        "fallback_reason": live_result.get(
            "error",
            "Live attraction provider unavailable.",
        ),
    }