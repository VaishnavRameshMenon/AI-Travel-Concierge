from sqlalchemy.orm import Session

from backend.app.database.models import Trip


def save_trip(db: Session, state):
    trip = Trip(
        user_query=state.get("user_query"),
        origin=state.get("origin"),
        destination=state.get("destination"),
        start_date=state.get("start_date"),
        end_date=state.get("end_date"),
        trip_duration_days=state.get("trip_duration_days"),
        travelers=state.get("travelers"),
        budget=state.get("budget"),
        interests=state.get("interests", []),
        itinerary=state.get("itinerary"),
        estimated_cost=state.get("estimated_cost"),
        weather_data=state.get("weather_data", {}),
        flight_data=state.get("flight_data", []),
        hotel_data=state.get("hotel_data", []),
        attraction_data=state.get("attraction_data", []),
    )

    db.add(trip)
    db.commit()
    db.refresh(trip)

    return trip


def update_trip(db: Session, trip: Trip, state):
    """
    Update an existing persisted trip with the latest generated/refined state.
    Used by the trip refinement endpoint so refinement does not create
    duplicate saved journeys.
    """

    trip.user_query = state.get("user_query", trip.user_query)
    trip.origin = state.get("origin", trip.origin)
    trip.destination = state.get("destination", trip.destination)
    trip.start_date = state.get("start_date", trip.start_date)
    trip.end_date = state.get("end_date", trip.end_date)
    trip.trip_duration_days = state.get(
        "trip_duration_days",
        trip.trip_duration_days,
    )
    trip.travelers = state.get("travelers", trip.travelers)
    trip.budget = state.get("budget", trip.budget)
    trip.interests = state.get("interests", trip.interests or [])

    trip.itinerary = state.get("itinerary", trip.itinerary)
    trip.estimated_cost = state.get(
        "estimated_cost",
        trip.estimated_cost,
    )

    trip.weather_data = state.get(
        "weather_data",
        trip.weather_data or {},
    )

    trip.flight_data = state.get(
        "flight_data",
        trip.flight_data or [],
    )

    trip.hotel_data = state.get(
        "hotel_data",
        trip.hotel_data or [],
    )

    trip.attraction_data = state.get(
        "attraction_data",
        trip.attraction_data or [],
    )

    db.add(trip)
    db.commit()
    db.refresh(trip)

    return trip


def get_trip(db: Session, trip_id: int):
    return (
        db.query(Trip)
        .filter(Trip.id == trip_id)
        .first()
    )


def get_all_trips(db: Session):
    return (
        db.query(Trip)
        .order_by(Trip.created_at.desc())
        .all()
    )