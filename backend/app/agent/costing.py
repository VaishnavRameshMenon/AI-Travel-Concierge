"""Deterministic trip cost floor from research data.

LLM estimated_cost is kept when it is at least this floor. Otherwise the
grounded figure replaces it.
"""

from __future__ import annotations

from typing import Any, Optional

# Documented local spend remainder (food, local transit, tickets) per traveler per day.
DAILY_LOCAL_INR = 3_500.0

# When origin and destination differ but no live flight price exists, add this
# per-traveler transport floor so international trips cannot collapse to local-only.
MISSING_FLIGHT_PER_TRAVELER_INR = 15_000.0


def _positive_prices(items: list[dict[str, Any]], *keys: str) -> list[float]:
    prices: list[float] = []
    for item in items:
        for key in keys:
            value = item.get(key)
            try:
                number = float(value)
            except (TypeError, ValueError):
                continue
            if number > 0:
                prices.append(number)
                break
    return prices


def research_cost_floor(
    flight_data: list[dict[str, Any]] | None,
    hotel_data: list[dict[str, Any]] | None,
    *,
    origin: str | None = None,
    destination: str | None = None,
    travelers: int | None = None,
    duration_days: int | None = None,
) -> dict[str, Any]:
    party = travelers if travelers and travelers > 0 else 1
    days = duration_days if duration_days and duration_days > 0 else 1
    flights = flight_data or []
    hotels = hotel_data or []

    flight_prices = _positive_prices(flights, "price", "total_price")
    hotel_prices = _positive_prices(hotels, "total_price", "price_per_night")

    cheapest_flight = min(flight_prices) if flight_prices else 0.0
    cheapest_hotel = 0.0
    if hotel_prices:
        # price_per_night is only used when no total_price exists on that item.
        total_priced = _positive_prices(hotels, "total_price")
        nightly = _positive_prices(
            [h for h in hotels if h.get("total_price") in (None, "")],
            "price_per_night",
        )
        candidates: list[float] = list(total_priced)
        candidates.extend(n * days for n in nightly)
        if candidates:
            cheapest_hotel = min(candidates)

    local = DAILY_LOCAL_INR * party * days

    missing_flight_floor = 0.0
    if (
        not flight_prices
        and origin
        and destination
        and origin.strip().lower() != destination.strip().lower()
    ):
        missing_flight_floor = MISSING_FLIGHT_PER_TRAVELER_INR * party

    floor = cheapest_flight + cheapest_hotel + local + missing_flight_floor

    return {
        "floor": round(floor, 2),
        "cheapest_flight": cheapest_flight or None,
        "cheapest_hotel": cheapest_hotel or None,
        "local_spend": local,
        "missing_flight_floor": missing_flight_floor or None,
        "daily_local_inr": DAILY_LOCAL_INR,
    }


def ground_estimated_cost(
    llm_cost: Optional[float],
    floor_info: dict[str, Any],
) -> tuple[float, bool]:
    """Return (grounded_cost, replaced)."""
    floor = float(floor_info.get("floor") or 0)
    if llm_cost is None or llm_cost <= 0:
        return floor, True
    if floor > 0 and llm_cost < floor:
        return floor, True
    return float(llm_cost), False
