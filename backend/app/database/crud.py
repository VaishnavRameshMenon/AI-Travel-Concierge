from sqlalchemy.orm import Session

from backend.app.database.models import Trip


def save_trip(db: Session, state: dict) -> Trip:
    trip = Trip(
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
    )

    db.add(trip)
    db.commit()
    db.refresh(trip)

    return trip


def get_trip(db: Session, trip_id: int):
    return db.query(Trip).filter(Trip.id == trip_id).first()


def get_all_trips(db: Session):
    return db.query(Trip).order_by(Trip.created_at.desc()).all()