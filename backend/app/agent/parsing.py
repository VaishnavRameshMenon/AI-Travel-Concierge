"""Deterministic parsers for INR budgets and trip dates.

These run after Gemini structured extraction so Indian currency formatting
and missing end dates do not depend on the model.
"""

from __future__ import annotations

import re
from datetime import date, timedelta
from typing import Optional

# Research-only fallback when the user gives a duration but no calendar dates.
# Documented product rule: search window starts 7 days from today.
DEFAULT_RESEARCH_OFFSET_DAYS = 7


_CURRENCY_TOKEN = r"(?:₹|rs\.?|inr|rupees?)"
_NUMBER = r"(\d{1,3}(?:,\d{2})+|\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)"


def parse_inr_budget(text: str | None) -> Optional[float]:
    """Parse an Indian-rupee budget from natural language.

    Handles ₹2,00,000, 2,50,000, Rs 2 lakh, 2.5 lakhs, 1 crore, 150000 rupees.
    """
    if not text:
        return None

    cleaned = text.lower().replace("\u20b9", "₹")
    cleaned = cleaned.replace("lakhs", "lakh").replace("crores", "crore")

    lakh_match = re.search(
        rf"(?:{_CURRENCY_TOKEN}\s*)?{_NUMBER}\s*lakh",
        cleaned,
        re.IGNORECASE,
    )
    if lakh_match:
        return _to_float(lakh_match.group(1)) * 100_000

    crore_match = re.search(
        rf"(?:{_CURRENCY_TOKEN}\s*)?{_NUMBER}\s*crore",
        cleaned,
        re.IGNORECASE,
    )
    if crore_match:
        return _to_float(crore_match.group(1)) * 10_000_000

    symbol_first = re.search(
        rf"{_CURRENCY_TOKEN}\s*{_NUMBER}",
        cleaned,
        re.IGNORECASE,
    )
    if symbol_first:
        return _to_float(symbol_first.group(1))

    number_then_currency = re.search(
        rf"{_NUMBER}\s*{_CURRENCY_TOKEN}",
        cleaned,
        re.IGNORECASE,
    )
    if number_then_currency:
        return _to_float(number_then_currency.group(1))

    indian_grouped = re.search(r"\b(\d{1,2},\d{2},\d{3})\b", cleaned)
    if indian_grouped:
        return _to_float(indian_grouped.group(1))

    return None


def _to_float(raw: str) -> Optional[float]:
    try:
        return float(raw.replace(",", ""))
    except (TypeError, ValueError):
        return None


def parse_iso_date(value: str | None) -> Optional[date]:
    if not value:
        return None
    from datetime import datetime

    text = value.strip()[:10]
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def derive_trip_dates(
    start_date: str | None,
    end_date: str | None,
    duration_days: int | None,
    *,
    today: date | None = None,
    allow_research_window: bool = True,
) -> tuple[Optional[str], Optional[str], Optional[int], Optional[str]]:
    """Fill missing start/end/duration when the other values are known.

    Returns (start, end, duration, warning).
    """
    warning: Optional[str] = None
    start = parse_iso_date(start_date)
    end = parse_iso_date(end_date)
    duration = duration_days if duration_days and duration_days > 0 else None

    if start and end:
        derived = (end - start).days + 1
        if derived <= 0:
            return start.isoformat(), end.isoformat(), duration, "End date is before start date."
        if duration is None:
            duration = derived
        return start.isoformat(), end.isoformat(), duration, None

    if start and duration:
        end = start + timedelta(days=duration - 1)
        return start.isoformat(), end.isoformat(), duration, None

    if end and duration:
        start = end - timedelta(days=duration - 1)
        return start.isoformat(), end.isoformat(), duration, None

    if duration and allow_research_window:
        today = today or date.today()
        start = today + timedelta(days=DEFAULT_RESEARCH_OFFSET_DAYS)
        end = start + timedelta(days=duration - 1)
        warning = (
            f"Trip calendar dates were not specified; using a research window "
            f"from {start.isoformat()} to {end.isoformat()} "
            f"({DEFAULT_RESEARCH_OFFSET_DAYS} days from today)."
        )
        return start.isoformat(), end.isoformat(), duration, warning

    return (
        start.isoformat() if start else start_date,
        end.isoformat() if end else end_date,
        duration,
        warning,
    )


def resolve_budget(user_query: str | None, extracted: float | None) -> Optional[float]:
    """Prefer a parsed INR amount from the query when extraction is missing or implausible."""
    parsed = parse_inr_budget(user_query)

    if parsed is None:
        return extracted if extracted and extracted > 0 else None

    if extracted is None or extracted <= 0:
        return parsed

    # Structured output sometimes returns 2 from "₹2,00,000".
    if extracted < 1000 and parsed >= 1000:
        return parsed

    if parsed / extracted >= 50:
        return parsed

    return extracted
