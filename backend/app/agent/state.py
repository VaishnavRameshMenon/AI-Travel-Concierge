import operator
from typing import Annotated, TypedDict, Optional, List, Dict, Any


class TravelState(TypedDict, total=False):
    # Original user request
    user_query: str

    # Trip requirements
    origin: Optional[str]
    origin_iata: Optional[str]

    destination: Optional[str]
    destination_iata: Optional[str]

    latitude: Optional[float]
    longitude: Optional[float]

    start_date: Optional[str]
    end_date: Optional[str]

    trip_duration_days: Optional[int]
    travelers: Optional[int]
    budget: Optional[float]

    interests: List[str]
    preferences: Dict[str, Any]

    # Research data
    flight_data: List[Dict[str, Any]]
    hotel_data: List[Dict[str, Any]]
    attraction_data: List[Dict[str, Any]]
    weather_data: Dict[str, Any]
    search_data: List[Dict[str, Any]]
    # Several research nodes run concurrently; combine their warnings safely.
    tool_warnings: Annotated[List[str], operator.add]

    # Generated itinerary
    itinerary: Optional[Dict[str, Any]]

    # Validation
    estimated_cost: Optional[float]
    constraint_violations: List[str]

    # Agent control
    required_tools: List[str]
    next_action: Optional[str]
    error: Optional[str]

    # Replanning
    replan_count: int

    # Final response
    final_response: Optional[str]
