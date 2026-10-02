"""Pydantic contracts for the public TripPilot API."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class TripGenerationRequest(BaseModel):
    user_query: str = Field(
        min_length=3,
        max_length=2_000,
        description="Natural-language travel request.",
        examples=[
            "Plan a 5-day food and culture trip from Delhi to Tokyo for two people."
        ],
    )


class TripGenerationResponse(BaseModel):
    success: bool = True
    persisted: bool = False
    trip_id: int | None = None
    destination: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    trip_duration_days: int | None = None
    travelers: int | None = None
    budget: float | None = None
    interests: list[str] = Field(default_factory=list)
    itinerary: dict[str, Any] | None = None
    estimated_cost: float | None = None
    weather_data: dict[str, Any] = Field(default_factory=dict)
    attraction_data: list[dict[str, Any]] = Field(default_factory=list)
    flight_data: list[dict[str, Any]] = Field(default_factory=list)
    hotel_data: list[dict[str, Any]] = Field(default_factory=list)
    tool_warnings: list[str] = Field(default_factory=list)
    constraint_violations: list[str] = Field(default_factory=list)
    final_response: str | None = None


class TripSummary(BaseModel):
    id: int
    destination: str
    trip_duration_days: int | None = None
    travelers: int | None = None
    budget: float | None = None
    estimated_cost: float | None = None
    created_at: datetime


class TripListResponse(BaseModel):
    count: int
    trips: list[TripSummary]


class TripDetailResponse(BaseModel):
    """Full trip record returned by GET /trips/{trip_id}."""

    id: int
    user_query: str | None = None
    origin: str | None = None
    destination: str
    start_date: str | None = None
    end_date: str | None = None
    trip_duration_days: int | None = None
    travelers: int | None = None
    budget: float | None = None
    interests: list[str] = Field(default_factory=list)
    itinerary: dict[str, Any] | None = None
    estimated_cost: float | None = None
    weather_data: dict[str, Any] = Field(default_factory=dict)
    flight_data: list[dict[str, Any]] = Field(default_factory=list)
    hotel_data: list[dict[str, Any]] = Field(default_factory=list)
    attraction_data: list[dict[str, Any]] = Field(default_factory=list)
    created_at: datetime


class HealthResponse(BaseModel):
    status: str
    database_configured: bool
