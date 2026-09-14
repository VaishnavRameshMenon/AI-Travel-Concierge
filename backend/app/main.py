import time
import uuid

from fastapi import Depends, FastAPI, HTTPException, Request
from sqlalchemy.orm import Session

from backend.app.agent.graph import travel_graph
from backend.app.database.crud import get_all_trips, get_trip, save_trip
from backend.app.database.database import SessionLocal
from backend.app.database.init_db import init_db
from backend.app.monitoring.logger import configure_logging, logger
from backend.app.monitoring.metrics import metrics


configure_logging()


app = FastAPI(
    title="TripPilot API",
    description="Backend API for the TripPilot AI Travel Concierge",
    version="1.0.0",
)


# ============================================================
# DATABASE
# ============================================================

@app.on_event("startup")
def startup():
    logger.info("application_startup")
    init_db()
    logger.info("database_initialized")


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# ============================================================
# REQUEST MONITORING MIDDLEWARE
# ============================================================

@app.middleware("http")
async def monitoring_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.perf_counter()

    try:
        response = await call_next(request)

        duration = time.perf_counter() - start_time
        success = response.status_code < 400

        metrics.record_request(
            duration=duration,
            success=success,
        )

        response.headers["X-Request-ID"] = request_id

        logger.info(
            "http_request",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_seconds=round(duration, 3),
        )

        return response

    except Exception as exc:
        duration = time.perf_counter() - start_time

        metrics.record_request(
            duration=duration,
            success=False,
        )

        logger.error(
            "http_request_failed",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            duration_seconds=round(duration, 3),
            error=str(exc),
        )

        raise


# ============================================================
# BASIC ENDPOINTS
# ============================================================

@app.get("/")
def root():
    return {
        "message": "TripPilot API is running",
        "status": "ok",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
    }


# ============================================================
# MONITORING
# ============================================================

@app.get("/metrics")
def get_metrics():
    return metrics.snapshot()


# ============================================================
# GENERATE TRIP
# ============================================================

@app.post("/trips/generate")
async def generate_trip(
    user_query: str,
    db: Session = Depends(get_db),
):
    start_time = time.perf_counter()

    logger.info(
        "trip_generation_started",
        user_query=user_query,
    )

    try:
        result = await travel_graph.ainvoke(
            {
                "user_query": user_query,
            }
        )

        duration = time.perf_counter() - start_time

        if result.get("error"):
            metrics.record_generation(
                duration=duration,
                success=False,
            )

            logger.error(
                "trip_generation_failed",
                duration_seconds=round(duration, 3),
                error=result["error"],
            )

            raise HTTPException(
                status_code=400,
                detail=result["error"],
            )

        trip = save_trip(db, result)

        metrics.record_generation(
            duration=duration,
            success=True,
        )

        logger.info(
            "trip_generation_completed",
            trip_id=trip.id,
            destination=result.get("destination"),
            duration_seconds=round(duration, 3),
            estimated_cost=result.get("estimated_cost"),
        )

        return {
            "success": True,
            "trip_id": trip.id,
            "destination": result.get("destination"),
            "trip_duration_days": result.get(
                "trip_duration_days"
            ),
            "travelers": result.get("travelers"),
            "budget": result.get("budget"),
            "interests": result.get("interests"),
            "itinerary": result.get("itinerary"),
            "estimated_cost": result.get(
                "estimated_cost"
            ),
            "constraint_violations": result.get(
                "constraint_violations",
                [],
            ),
        }

    except HTTPException:
        raise

    except Exception as exc:
        duration = time.perf_counter() - start_time

        metrics.record_generation(
            duration=duration,
            success=False,
        )

        logger.exception(
            "trip_generation_exception",
            duration_seconds=round(duration, 3),
            error=str(exc),
        )

        raise HTTPException(
            status_code=500,
            detail=f"Trip generation failed: {str(exc)}",
        )


# ============================================================
# GET ONE TRIP
# ============================================================

@app.get("/trips/{trip_id}")
def fetch_trip(
    trip_id: int,
    db: Session = Depends(get_db),
):
    logger.info(
        "trip_fetch_started",
        trip_id=trip_id,
    )

    trip = get_trip(db, trip_id)

    if not trip:
        logger.warning(
            "trip_not_found",
            trip_id=trip_id,
        )

        raise HTTPException(
            status_code=404,
            detail="Trip not found",
        )

    return {
        "id": trip.id,
        "destination": trip.destination,
        "start_date": trip.start_date,
        "end_date": trip.end_date,
        "trip_duration_days": trip.trip_duration_days,
        "travelers": trip.travelers,
        "budget": trip.budget,
        "interests": trip.interests,
        "itinerary": trip.itinerary,
        "estimated_cost": trip.estimated_cost,
        "weather_data": trip.weather_data,
        "created_at": trip.created_at,
    }


# ============================================================
# GET ALL TRIPS
# ============================================================

@app.get("/trips")
def fetch_trips(
    db: Session = Depends(get_db),
):
    trips = get_all_trips(db)

    logger.info(
        "trips_listed",
        count=len(trips),
    )

    return {
        "count": len(trips),
        "trips": [
            {
                "id": trip.id,
                "destination": trip.destination,
                "trip_duration_days": trip.trip_duration_days,
                "travelers": trip.travelers,
                "budget": trip.budget,
                "estimated_cost": trip.estimated_cost,
                "created_at": trip.created_at,
            }
            for trip in trips
        ],
    }