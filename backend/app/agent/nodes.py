from typing import Optional, List

from pydantic import BaseModel, Field

from backend.app.agent.state import TravelState
from backend.app.agent.llm import llm


# ============================================================
# STRUCTURED OUTPUT MODELS
# ============================================================

class TripRequirements(BaseModel):
    origin: Optional[str] = Field(
        default=None,
        description=(
            "The city or airport the traveler is departing from. "
            "Only extract if explicitly provided."
        ),
    )

    destination: Optional[str] = Field(
        default=None,
        description="The destination the user wants to visit",
    )

    start_date: Optional[str] = Field(
        default=None,
        description="Trip start date if explicitly provided",
    )

    end_date: Optional[str] = Field(
        default=None,
        description="Trip end date if explicitly provided",
    )

    trip_duration_days: Optional[int] = Field(
        default=None,
        description=(
            "Number of days for the trip, such as 7 for "
            "'7 days'"
        ),
    )

    travelers: Optional[int] = Field(
        default=None,
        description="Number of travelers",
    )

    budget: Optional[float] = Field(
        default=None,
        description="Maximum trip budget",
    )

    interests: List[str] = Field(
        default_factory=list,
        description=(
            "User interests such as food, anime, "
            "nature, photography"
        ),
    )


class Itinerary(BaseModel):
    title: str = Field(
        description="Short title for the trip"
    )

    summary: str = Field(
        description="Short summary of the itinerary"
    )

    estimated_cost: float = Field(
        description=(
            "Estimated total trip cost in the user's currency"
        )
    )

    days: List[dict] = Field(
        description=(
            "Day-by-day itinerary with exactly the "
            "requested number of days"
        )
    )


structured_llm = llm.with_structured_output(
    TripRequirements
)

itinerary_llm = llm.with_structured_output(
    Itinerary
)


# ============================================================
# PLANNER
# ============================================================

def planner_node(state: TravelState) -> TravelState:
    user_query = state.get("user_query", "")

    prompt = f"""
You are the planning component of TripPilot,
an AI travel concierge.

Extract the travel requirements explicitly provided
by the user.

Rules:

1. Never invent missing information.

2. Missing values must be null.

3. Extract the departure/origin city or airport
   if the user explicitly provides one.

4. Extract the destination.

5. Extract start and end dates if explicitly provided.

6. IMPORTANT:
   If the user says:
   - "for 7 days"
   - "7-day trip"
   - "a week"

   extract trip_duration_days as 7.

7. Do not calculate or invent dates when only a
   duration is provided.

8. Extract the number of travelers.

9. Extract the budget.

10. Extract relevant interests.

11. If the user says:
    "from Delhi to Tokyo"

    then:
    origin = "Delhi"
    destination = "Tokyo"

12. If the user only says:
    "I want to travel to Tokyo"

    then:
    origin = null
    destination = "Tokyo"

User request:
{user_query}
"""

    requirements = structured_llm.invoke(prompt)

    return {
        "origin": requirements.origin,
        "destination": requirements.destination,

        "start_date": requirements.start_date,
        "end_date": requirements.end_date,

        "trip_duration_days": (
            requirements.trip_duration_days
        ),

        "travelers": requirements.travelers,
        "budget": requirements.budget,
        "interests": requirements.interests,

        "constraint_violations": [],
        "replan_count": 0,
        "next_action": "research",
        "error": None,
    }


# ============================================================
# RESEARCH PLANNER
# ============================================================

def research_node(state: TravelState) -> TravelState:
    required_tools = []

    destination = state.get("destination")

    if destination:
        required_tools.extend([
            "attractions",
            "weather",
        ])

    if (
        state.get("origin")
        and destination
        and state.get("start_date")
        and state.get("end_date")
    ):
        required_tools.append("flights")

    if (
        destination
        and state.get("start_date")
        and state.get("end_date")
    ):
        required_tools.append("hotels")

    if destination:
        required_tools.append("search")

    if not required_tools:
        return {
            "required_tools": [],
            "next_action": "ask_user",
        }

    return {
        "required_tools": required_tools,
        "next_action": "research",
    }


# ============================================================
# GEOCODING
# ============================================================

async def geocoder_node(state: TravelState) -> TravelState:
    from backend.app.tools.weather import geocode_destination

    destination = state.get("destination")

    if not destination:
        return {
            "error": "Destination is missing.",
            "next_action": "ask_user",
        }

    location = await geocode_destination(
        destination
    )

    if location.get("error"):
        return {
            "error": location["error"],
            "next_action": "ask_user",
        }

    return {
        "latitude": location.get("latitude"),
        "longitude": location.get("longitude"),
        "error": None,
    }


# ============================================================
# WEATHER
# ============================================================

async def weather_node(state: TravelState) -> TravelState:
    from backend.app.tools.weather import get_weather

    latitude = state.get("latitude")
    longitude = state.get("longitude")

    if latitude is None or longitude is None:
        return {
            "weather_data": {},
            "error": (
                "Destination coordinates are missing."
            ),
        }

    weather_data = await get_weather(
        latitude,
        longitude,
    )

    return {
        "weather_data": weather_data,
    }


# ============================================================
# ATTRACTIONS
# ============================================================

async def attractions_node(
    state: TravelState,
) -> TravelState:
    from backend.app.tools.attractions import (
        search_attractions,
    )

    latitude = state.get("latitude")
    longitude = state.get("longitude")

    result = await search_attractions(
        latitude=latitude,
        longitude=longitude,
        interests=state.get("interests", []),
    )

    if result.get("success"):
        return {
            "attraction_data": result.get(
                "attractions",
                [],
            )
        }

    return {
        "attraction_data": [],
        "error": result.get("error"),
    }


# ============================================================
# FLIGHTS
# ============================================================

async def flights_node(
    state: TravelState,
) -> TravelState:
    from backend.app.tools.flights import (
        search_flights,
        find_airport_iata,
    )

    origin = state.get("origin")
    destination = state.get("destination")

    if not origin:
        return {
            "flight_data": [],
            "error": (
                "Departure location is required "
                "for flight search."
            ),
        }

    if not destination:
        return {
            "flight_data": [],
            "error": (
                "Destination is required "
                "for flight search."
            ),
        }

    # --------------------------------------------------------
    # Find origin airport
    # --------------------------------------------------------

    origin_airport = await find_airport_iata(
        origin
    )

    if not origin_airport.get("success"):
        return {
            "flight_data": [],
            "error": origin_airport.get(
                "error",
                f"Could not find airport for {origin}.",
            ),
        }

    # --------------------------------------------------------
    # Find destination airport
    # --------------------------------------------------------

    destination_airport = await find_airport_iata(
        destination
    )

    if not destination_airport.get("success"):
        return {
            "flight_data": [],
            "error": destination_airport.get(
                "error",
                (
                    "Could not find airport for "
                    f"{destination}."
                ),
            ),
        }

    origin_iata = origin_airport.get(
        "iata"
    )

    destination_iata = destination_airport.get(
        "iata"
    )

    # --------------------------------------------------------
    # Search flights
    # --------------------------------------------------------

    result = await search_flights(
        departure_iata=origin_iata,
        arrival_iata=destination_iata,
        flight_date=state.get("start_date"),
    )

    if not result.get("success"):
        return {
            "origin_iata": origin_iata,
            "destination_iata": destination_iata,
            "flight_data": [],
            "error": result.get(
                "error",
                "Flight search failed.",
            ),
        }

    return {
        "origin_iata": origin_iata,
        "destination_iata": destination_iata,
        "flight_data": result.get(
            "flights",
            [],
        ),
        "error": None,
    }


# ============================================================
# HOTELS
# ============================================================

async def hotels_node(
    state: TravelState,
) -> TravelState:
    from backend.app.tools.hotels import (
        search_hotels,
    )

    destination = state.get("destination")

    if not destination:
        return {
            "hotel_data": [],
        }

    result = await search_hotels(
        destination=destination,
        check_in=state.get("start_date"),
        check_out=state.get("end_date"),
        travelers=state.get("travelers"),
        budget=state.get("budget"),
    )

    if result.get("success"):
        return {
            "hotel_data": result.get(
                "hotels",
                []
            )
        }

    return {
        "hotel_data": [],
        "error": result.get("error"),
    }


# ============================================================
# RESEARCH ROUTER
# ============================================================

def route_research(state: TravelState):
    required_tools = state.get(
        "required_tools",
        [],
    )

    destinations = []

    if "weather" in required_tools:
        destinations.append("weather")

    if "attractions" in required_tools:
        destinations.append("attractions")

    if "flights" in required_tools:
        destinations.append("flights")

    if "hotels" in required_tools:
        destinations.append("hotels")

    if not destinations:
        return "end"

    return destinations


def research_complete_node(
    state: TravelState,
) -> TravelState:
    return {
        "next_action": "build_itinerary"
    }


# ============================================================
# ITINERARY
# ============================================================

def itinerary_node(
    state: TravelState,
) -> TravelState:

    destination = state.get("destination")
    origin = state.get("origin")

    travelers = state.get("travelers")
    budget = state.get("budget")
    interests = state.get("interests", [])

    start_date = state.get("start_date")
    end_date = state.get("end_date")
    duration = state.get("trip_duration_days")

    weather_data = state.get(
        "weather_data",
        {},
    )

    attraction_data = state.get(
        "attraction_data",
        [],
    )

    flight_data = state.get(
        "flight_data",
        [],
    )

    hotel_data = state.get(
        "hotel_data",
        [],
    )

    prompt = f"""
You are the itinerary generation component
of TripPilot.

Create a realistic and practical travel itinerary.

TRIP REQUIREMENTS

Origin:
{origin}

Destination:
{destination}

Travelers:
{travelers}

Budget:
{budget}

Interests:
{interests}

Start date:
{start_date}

End date:
{end_date}

Trip duration:
{duration} days


WEATHER DATA
{weather_data}


ATTRACTION DATA
{attraction_data}


FLIGHT DATA
{flight_data}


HOTEL DATA
{hotel_data}


RULES

1. The itinerary MUST contain exactly
   {duration if duration else "a sensible number of"} days.

2. If trip duration is provided, do not generate
   fewer or more days.

3. Respect the user's interests.

4. Consider weather when planning activities.

5. Do not invent actual flight or hotel bookings.

6. Only mention flight information that appears
   in the provided flight data.

7. Only mention hotel information that appears
   in the provided hotel data.

8. Avoid overloading each day.

9. Group activities logically by location.

10. Estimate the total cost realistically.

11. Stay within the user's budget whenever possible.

12. If attraction data is unavailable, clearly
    provide general suggestions.

13. If exact dates are unavailable but duration
    is known, number the days from Day 1 onward.

14. If no flight data is available, do not pretend
    that a flight was found.

15. If no hotel data is available, do not pretend
    that a hotel was booked.

Return:

- Trip title
- Trip summary
- Estimated total cost
- Day-by-day itinerary
"""

    itinerary = itinerary_llm.invoke(prompt)

    return {
        "itinerary": {
            "title": itinerary.title,
            "summary": itinerary.summary,
            "estimated_cost": itinerary.estimated_cost,
            "days": itinerary.days,
        },

        "estimated_cost": itinerary.estimated_cost,

        "constraint_violations": [],

        "next_action": "validate",

        "error": None,
    }


# ============================================================
# CONSTRAINT CHECKER
# ============================================================

def constraint_checker_node(
    state: TravelState,
) -> TravelState:

    violations = []

    destination = state.get("destination")
    travelers = state.get("travelers")
    budget = state.get("budget")
    duration = state.get("trip_duration_days")

    itinerary = state.get("itinerary")
    estimated_cost = state.get("estimated_cost")

    if not destination:
        violations.append(
            "Destination is missing."
        )

    if travelers is not None and travelers < 1:
        violations.append(
            "Number of travelers must be at least 1."
        )

    if budget is not None and budget <= 0:
        violations.append(
            "Budget must be greater than zero."
        )

    if not itinerary:
        violations.append(
            "No itinerary was generated."
        )

    if duration and itinerary:
        actual_days = len(
            itinerary.get("days", [])
        )

        if actual_days != duration:
            violations.append(
                f"Itinerary contains {actual_days} "
                f"days but {duration} days were requested."
            )

    if (
        budget is not None
        and estimated_cost is not None
        and estimated_cost > budget
    ):
        violations.append(
            f"Estimated trip cost ({estimated_cost}) "
            f"exceeds the budget ({budget})."
        )

    if violations:
        return {
            "constraint_violations": violations,
            "next_action": "replan",
        }

    return {
        "constraint_violations": [],
        "next_action": "complete",
    }


# ============================================================
# VALIDATION ROUTER
# ============================================================

def route_after_validation(
    state: TravelState,
):
    violations = state.get(
        "constraint_violations",
        [],
    )

    replan_count = state.get(
        "replan_count",
        0,
    )

    if violations and replan_count < 2:
        return "replan"

    return "complete"


# ============================================================
# REPLANNER
# ============================================================

def replanner_node(
    state: TravelState,
) -> TravelState:

    violations = state.get(
        "constraint_violations",
        [],
    )

    current_itinerary = state.get(
        "itinerary",
        {},
    )

    duration = state.get(
        "trip_duration_days"
    )

    budget = state.get(
        "budget"
    )

    prompt = f"""
You are the replanning component of TripPilot.

The current itinerary failed validation.

CONSTRAINT VIOLATIONS:
{violations}

CURRENT ITINERARY:
{current_itinerary}

USER REQUIREMENTS:

Origin:
{state.get("origin")}

Destination:
{state.get("destination")}

Travelers:
{state.get("travelers")}

Budget:
{budget}

Interests:
{state.get("interests", [])}

Trip duration:
{duration} days

Create a revised itinerary.

Requirements:

- Fix every listed constraint violation.
- The itinerary MUST contain exactly
  {duration} days when duration is provided.
- If the itinerary exceeds the budget,
  reduce unnecessary activities.
- Preserve the user's important interests.
- Keep the itinerary realistic.
- Do not invent actual bookings.
- Keep the revised estimated cost within
  the budget when possible.

Return the complete revised itinerary.
"""

    revised = itinerary_llm.invoke(
        prompt
    )

    new_count = (
        state.get("replan_count", 0) + 1
    )

    return {
        "itinerary": {
            "title": revised.title,
            "summary": revised.summary,
            "estimated_cost": revised.estimated_cost,
            "days": revised.days,
        },

        "estimated_cost": revised.estimated_cost,

        "replan_count": new_count,

        "constraint_violations": [],

        "next_action": "validate",

        "error": None,
    }