import asyncio
import os
from typing import Any, Dict, List
from urllib.parse import quote_plus

import httpx
from dotenv import load_dotenv

load_dotenv()

OPENTRIPMAP_API_KEY = os.getenv("OPENTRIPMAP_API_KEY")
OPENTRIPMAP_BASE_URL = "https://api.opentripmap.com/0.1"

FALLBACK_IMAGES = {
    "anime": "https://images.unsplash.com/photo-1578632767115-351597cf2477?auto=format&fit=crop&w=1200&q=82",
    "food": "https://images.unsplash.com/photo-1547592180-85f173990554?auto=format&fit=crop&w=1200&q=82",
    "photography": "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1200&q=82",
    "culture": "https://images.unsplash.com/photo-1528360983277-13d401cdc186?auto=format&fit=crop&w=1200&q=82",
    "landmark": "https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?auto=format&fit=crop&w=1200&q=82",
}


def _maps_search_url(name: str) -> str:
    return f"https://www.google.com/maps/search/?api=1&query={quote_plus(name)}"


def _fallback_place(name: str, category: str, destination: str = "") -> Dict[str, Any]:
    search_name = f"{name} {destination}".strip()
    return {
        "name": name,
        "category": category,
        "source": "fallback",
        "image_url": FALLBACK_IMAGES.get(category, FALLBACK_IMAGES["landmark"]),
        "maps_url": _maps_search_url(search_name),
        "description": f"A {category} recommendation for exploring {destination or 'the destination'}.",
    }


def fallback_attractions(
    interests: List[str] | None = None,
    destination: str = "",
) -> List[Dict[str, Any]]:
    interests = interests or []
    normalized = {str(i).lower().strip() for i in interests}
    attractions: List[Dict[str, Any]] = []

    if normalized.intersection({"anime", "manga", "gaming", "otaku"}):
        attractions.append(_fallback_place("Anime and pop-culture districts", "anime", destination))

    if normalized.intersection({"food", "cuisine", "restaurants", "street food"}):
        attractions.append(_fallback_place("Local food districts and markets", "food", destination))

    if normalized.intersection({"photography", "photo", "nature", "scenery"}):
        attractions.append(_fallback_place("Scenic photography locations", "photography", destination))

    attractions.extend([
        _fallback_place("Local cultural attractions", "culture", destination),
        _fallback_place("Popular city landmarks", "landmark", destination),
    ])

    return attractions


async def _fetch_place_details(client: httpx.AsyncClient, xid: str) -> Dict[str, Any]:
    url = f"{OPENTRIPMAP_BASE_URL}/en/places/xid/{xid}"
    response = await client.get(url, params={"apikey": OPENTRIPMAP_API_KEY})
    response.raise_for_status()
    data = response.json()
    return data if isinstance(data, dict) else {}


async def search_opentripmap(
    latitude: float,
    longitude: float,
    radius: int = 5000,
    limit: int = 20,
) -> Dict[str, Any]:
    if not OPENTRIPMAP_API_KEY:
        return {"success": False, "error": "OpenTripMap API key is not configured."}

    url = f"{OPENTRIPMAP_BASE_URL}/places/radius"
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
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if isinstance(data, dict) and data.get("error"):
                return {"success": False, "error": data.get("error")}

            places: List[Dict[str, Any]] = []
            for place in data if isinstance(data, list) else []:
                if not isinstance(place, dict):
                    continue

                point = place.get("point") or {}
                name = place.get("name") or "Unnamed attraction"
                places.append({
                    "name": name,
                    "category": place.get("kinds"),
                    "latitude": point.get("lat"),
                    "longitude": point.get("lon"),
                    "xid": place.get("xid"),
                    "source": "opentripmap",
                    "maps_url": _maps_search_url(name),
                })

            enrichable = [p for p in places[:8] if p.get("xid")]
            if enrichable:
                details = await asyncio.gather(
                    *[_fetch_place_details(client, str(p["xid"])) for p in enrichable],
                    return_exceptions=True,
                )

                for place, detail in zip(enrichable, details):
                    if isinstance(detail, Exception):
                        continue

                    extracts = detail.get("wikipedia_extracts") or {}
                    preview = detail.get("preview") or {}
                    description = extracts.get("text")
                    image_url = preview.get("source")
                    website = detail.get("url")
                    wikipedia = detail.get("wikipedia")

                    if description:
                        place["description"] = description
                    if image_url:
                        place["image_url"] = image_url
                    if website:
                        place["website"] = website
                    if wikipedia:
                        place["wikipedia"] = wikipedia

            return {"success": True, "provider": "opentripmap", "attractions": places}

    except httpx.HTTPStatusError as exc:
        return {"success": False, "error": f"OpenTripMap returned HTTP {exc.response.status_code}."}
    except httpx.HTTPError as exc:
        return {"success": False, "error": "OpenTripMap service unavailable.", "details": str(exc)}
    except Exception as exc:
        return {"success": False, "error": "Unexpected OpenTripMap error.", "details": str(exc)}


async def search_attractions(
    latitude: float,
    longitude: float,
    interests: List[str] | None = None,
    destination: str = "",
) -> Dict[str, Any]:
    if latitude is None or longitude is None:
        return {
            "success": False,
            "provider": "fallback",
            "error": "Destination coordinates are required.",
            "attractions": fallback_attractions(interests, destination),
        }

    live_result = await search_opentripmap(latitude=latitude, longitude=longitude)

    if live_result.get("success") and live_result.get("attractions"):
        return live_result

    return {
        "success": True,
        "provider": "fallback",
        "attractions": fallback_attractions(interests, destination),
        "fallback_reason": live_result.get("error", "Live attraction provider unavailable."),
    }
