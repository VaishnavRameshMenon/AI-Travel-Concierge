from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.database.database import Base


class Trip(Base):
    __tablename__ = "trips"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    # ── original request ──────────────────────────────────────
    user_query: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ── parsed trip parameters ────────────────────────────────
    origin: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    destination: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    start_date: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    end_date: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    trip_duration_days: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    travelers: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    budget: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    interests: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    # ── AI-generated outputs ──────────────────────────────────
    itinerary: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    estimated_cost: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # ── research data ─────────────────────────────────────────
    weather_data: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    flight_data: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    hotel_data: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    attraction_data: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    # ── metadata ──────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )