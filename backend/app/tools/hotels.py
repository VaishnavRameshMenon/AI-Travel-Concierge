from typing import Dict, Any


async def search_hotels(
    destination: str,
    check_in: str | None = None,
    check_out: str | None = None,
    travelers: int | None = None,
    budget: float | None = None,
) -> Dict[str, Any]:
    """
    Hotel search provider.

    Returns structured fallback data when a live hotel provider
    is not configured yet.
    """

    if not destination:
        return {
            "success": False,
            "error": "Destination is required.",
            "hotels": [],
        }

    hotels = [
        {
            "name": f"Recommended hotel in {destination}",
            "location": destination,
            "estimated_price_per_night": 8000,
            "rating": 4.0,
            "source": "fallback",
        },
        {
            "name": f"Budget hotel in {destination}",
            "location": destination,
            "estimated_price_per_night": 5000,
            "rating": 3.5,
            "source": "fallback",
        },
    ]

    return {
        "success": True,
        "provider": "fallback",
        "hotels": hotels,
        "message": "Live hotel provider unavailable; fallback hotel options used.",
    }