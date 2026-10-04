from datetime import date
from typing import Optional, List

from pydantic import BaseModel, Field

from backend.app.agent.costing import ground_estimated_cost, research_cost_floor
from backend.app.agent.llm import get_resilient_structured_llm
from backend.app.agent.parsing import derive_trip_dates, resolve_budget
from backend.app.agent.state import TravelState


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
        description="Trip start date in YYYY-MM-DD if explicitly provided",
    )
    end_date: Optional[str] = Field(
        default=None,
        description="Trip end date in YYYY-MM-DD if explicitly provided",
    )
    trip_duration_days: Optional[int] = Field(
        default=None,
        description="Number of days for the trip, such as 7 for '7 days'",
    )
    travelers: Optional[int] = Field(
        default=None,
        description="Number of travelers",
    )
    budget: Optional[float] = Field(
        default=None,
        description=(
            "Maximum trip budget as a plain number in INR. "
            "₹2,00,000 is 200000. 2 lakh is 200000. Never drop Indian grouping."
        ),
    )
    interests: List[str] = Field(
        default_factory=list,
        description="User interests such as food, anime, nature, photography",
    )


class Itinerary(BaseModel):
    title: str = Field(description="Short title for the trip")
    summary: str = Field(description="Short summary of the itinerary")
    estimated_cost: float = Field(
        description="Estimated total trip cost in INR, including transport and stay"
    )
    days: List[dict] = Field(
        description="Day-by-day itinerary with exactly the requested number of days"
    )


structured_llm = get_resilient_structured_llm(TripRequirements)
itinerary_llm = get_resilient_structured_llm(Itinerary)


def _keep(previous, extracted):
    if extracted is not None and extracted != "" and extracted != []:
        return extracted
    return previous


def planner_node(state: TravelState) -> TravelState:
    user_query = state.get("user_query", "")
    refinement = state.get("refinement_instruction")

    prompt = f"""
You are the planning component of TripPilot,
an AI travel concierge.

Extract the travel requirements explicitly provided
by the user.

Rules:

1. Never invent missing information.
2. Missing values must be null.
3. Extract origin and destination city names without extra commentary.
4. Dates must be YYYY-MM-DD when the user gives a calendar date.
5. If the user says "for 7 days" / "7-day trip" / "a week",
   extract trip_duration_days as 7.
6. Do not invent calendar dates when only a duration is provided.
7. Extract travelers.
8. Extract budget as a numeric INR amount:
   - ₹2,00,000 or Rs 2,00,000 = 200000
   - 2 lakh / 2 lakhs = 200000
   - 2.5 lakh = 250000
   - 150000 rupees = 150000
9. Extract relevant interests.
10. "from Delhi to Tokyo" => origin Delhi, destination Tokyo.

User request:
{user_query}

Refinement instruction (may be empty):
{refinement or "None"}
"""

    requirements = structured_llm.invoke(prompt)

    duration = requirements.trip_duration_days
    if duration is None and requirements.start_date and requirements.end_date:
        try:
            duration = (
                date.fromisoformat(requirements.end_date)
                - date.fromisoformat(requirements.start_date)
            ).days + 1
        except ValueError:
            pass

    origin = _keep(state.get("origin"), requirements.origin)
    destination = _keep(state.get("destination"), requirements.destination)
    travelers = _keep(state.get("travelers"), requirements.travelers)
    interests = requirements.interests or state.get("interests") or []

    budget = resolve_budget(user_query, requirements.budget)
    if budget is None:
        budget = state.get("budget")
    if refinement and state.get("user_query"):
        combined = f"{state.get('user_query')} {user_query} {refinement}"
        budget = resolve_budget(combined, budget)

    start_date, end_date, duration, date_warning = derive_trip_dates(
        _keep(state.get("start_date"), requirements.start_date),
        _keep(state.get("end_date"), requirements.end_date),
        duration if duration is not None else state.get("trip_duration_days"),
    )

    warnings: list[str] = []
    if date_warning:
        warnings.append(date_warning)

    return {
        "origin": origin,
        "destination": destination,
        "start_date": start_date,
        "end_date": end_date,
        "trip_duration_days": duration,
        "travelers": travelers,
        "budget": budget,
        "interests": interests,
        "constraint_violations": [],
        "tool_warnings": warnings,
        "replan_count": 0,
        "next_action": "research",
        "error": None,
        "refinement_instruction": refinement,
        "previous_itinerary": state.get("previous_itinerary"),
    }


def research_node(state: TravelState) -> TravelState:
    required_tools = []
    destination = state.get("destination")
    origin = state.get("origin")
    start_date = state.get("start_date")
    end_date = state.get("end_date")

    if destination:
        required_tools.extend(["attractions", "weather"])

    if origin and destination and start_date:
        required_tools.append("flights")

    if destination and start_date and end_date:
        required_tools.append("hotels")

    if not required_tools:
        return {
            "required_tools": [],
            "next_action": "ask_user",
        }

    return {
        "required_tools": required_tools,
        "next_action": "research",
    }


async def geocoder_node(state: TravelState) -> TravelState:
    from backend.app.tools.weather import geocode_destination

    destination = state.get("destination")

    if not destination:
        return {
            "error": "Destination is missing.",
            "next_action": "ask_user",
        }

    location = await geocode_destination(destination)

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


async def weather_node(state: TravelState) -> TravelState:
    from backend.app.tools.weather import get_weather

    latitude = state.get("latitude")
    longitude = state.get("longitude")

    if latitude is None or longitude is None:
        return {
            "weather_data": {},
            "error": "Destination coordinates are missing.",
        }

    weather_data = await get_weather(
        latitude,
        longitude,
        state.get("start_date"),
        state.get("end_date"),
    )

    if weather_data.get("error"):
        return {
            "weather_data": {},
            "tool_warnings": [weather_data["error"]],
        }

    if weather_data.get("warning"):
        return {
            "weather_data": weather_data,
            "tool_warnings": [weather_data["warning"]],
        }

    return {"weather_data": weather_data}


async def attractions_node(state: TravelState) -> TravelState:
    from backend.app.tools.attractions import search_attractions

    result = await search_attractions(
        latitude=state.get("latitude"),
        longitude=state.get("longitude"),
        interests=state.get("interests", []),
    )

    if result.get("success"):
        update = {
            "attraction_data": result.get("attractions", []),
        }
        if result.get("fallback_reason"):
            update["tool_warnings"] = [result["fallback_reason"]]
        return update

    return {
        "attraction_data": result.get("attractions", []),
        "tool_warnings": [result.get("error", "Attraction search failed.")],
    }


async def flights_node(state: TravelState) -> TravelState:
    from backend.app.tools.flights import search_flights

    origin = state.get("origin")
    destination = state.get("destination")
    start_date = state.get("start_date")
    end_date = state.get("end_date")
    travelers = state.get("travelers") or 1

    if not origin or not destination:
        return {"flight_data": []}

    if not start_date:
        return {
            "flight_data": [],
            "tool_warnings": ["Flight search requires a departure date."],
        }

    result = await search_flights(
        origin=origin,
        destination=destination,
        departure_date=start_date,
        return_date=end_date,
        travelers=travelers,
    )

    flights = result.get("flights", [])
    search_parameters = result.get("search_parameters", {})

    update = {
        "origin_iata": search_parameters.get("origin_iata"),
        "destination_iata": search_parameters.get("destination_iata"),
        "flight_data": flights,
    }

    warning = result.get("warning")
    if warning:
        update["tool_warnings"] = [warning]

    return update


async def hotels_node(state: TravelState) -> TravelState:
    from backend.app.tools.hotels import search_hotels

    destination = state.get("destination")

    if not destination:
        return {"hotel_data": []}

    result = await search_hotels(
        destination=destination,
        check_in_date=state.get("start_date"),
        check_out_date=state.get("end_date"),
        travelers=state.get("travelers") or 1,
        budget=state.get("budget"),
    )

    update = {"hotel_data": result.get("hotels", [])}
    warning = result.get("warning")
    if warning:
        update["tool_warnings"] = [warning]
    return update


def route_research(state: TravelState):
    required_tools = state.get("required_tools", [])
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


def research_complete_node(state: TravelState) -> TravelState:
    return {"next_action": "build_itinerary"}


def _apply_grounded_cost(state: TravelState, itinerary) -> dict:
    floor_info = research_cost_floor(
        state.get("flight_data") or [],
        state.get("hotel_data") or [],
        origin=state.get("origin"),
        destination=state.get("destination"),
        travelers=state.get("travelers"),
        duration_days=state.get("trip_duration_days"),
    )
    grounded, replaced = ground_estimated_cost(
        itinerary.estimated_cost,
        floor_info,
    )
    warnings = []
    if replaced:
        warnings.append(
            "Estimated cost was raised to a research-based floor so it is not "
            "lower than live flight/hotel prices plus a local daily remainder."
        )

    payload = {
        "title": itinerary.title,
        "summary": itinerary.summary,
        "estimated_cost": grounded,
        "days": itinerary.days,
        "cost_breakdown": floor_info,
    }
    destination = state.get("destination")
    update = {
        "itinerary": payload,
        "estimated_cost": grounded,
        "constraint_violations": [],
        "next_action": "validate",
        "final_response": (
            f"Your itinerary for {destination} is ready. "
            f"Estimated total cost: {grounded}."
        ),
    }
    if warnings:
        update["tool_warnings"] = warnings
    return update


def itinerary_node(state: TravelState) -> TravelState:
    destination = state.get("destination")
    duration = state.get("trip_duration_days")
    refinement = state.get("refinement_instruction")
    previous = state.get("previous_itinerary")

    prompt = f"""
You are the itinerary generation component of TripPilot.
Create a realistic and practical travel itinerary.

TRIP REQUIREMENTS
Origin: {state.get("origin")}
Destination: {destination}
Travelers: {state.get("travelers")}
Budget: {state.get("budget")}
Interests: {state.get("interests", [])}
Start date: {state.get("start_date")}
End date: {state.get("end_date")}
Trip duration: {duration} days

WEATHER DATA
{state.get("weather_data", {})}

ATTRACTION DATA
{state.get("attraction_data", [])}

FLIGHT DATA
{state.get("flight_data", [])}

HOTEL DATA
{state.get("hotel_data", [])}

PREVIOUS ITINERARY
{previous}

REFINEMENT INSTRUCTION
{refinement or "None — generate a new itinerary."}

RULES
1. The itinerary MUST contain exactly {duration if duration else "a sensible number of"} days.
2. If a refinement instruction is present, apply it to the previous itinerary
   while keeping origin, destination, dates, travelers, and budget unless the
   instruction explicitly changes them.
3. Respect the user's interests.
4. Consider weather when planning activities.
5. Do not invent actual flight or hotel bookings.
6. Only mention flight/hotel information that appears in the provided data.
7. Estimate total cost in INR using the provided flight and hotel prices
   plus realistic local spend. Do not return a token local-only amount
   when transport or hotels are required.
8. Stay within the user's budget whenever possible without ignoring
   real transport/stay prices.

Return trip title, summary, estimated total cost, and day-by-day itinerary.
Each day object should include title, summary, and activities.
"""

    itinerary = itinerary_llm.invoke(prompt)
    return _apply_grounded_cost(state, itinerary)


def constraint_checker_node(state: TravelState) -> TravelState:
    violations = []

    destination = state.get("destination")
    travelers = state.get("travelers")
    budget = state.get("budget")
    duration = state.get("trip_duration_days")
    itinerary = state.get("itinerary")
    estimated_cost = state.get("estimated_cost")

    if not destination:
        violations.append("Destination is missing.")

    if travelers is not None and travelers < 1:
        violations.append("Number of travelers must be at least 1.")

    if budget is not None and budget <= 0:
        violations.append("Budget must be greater than zero.")

    if not itinerary:
        violations.append("No itinerary was generated.")

    if duration and itinerary:
        actual_days = len(itinerary.get("days", []))
        if actual_days != duration:
            violations.append(
                f"Itinerary contains {actual_days} days but {duration} days were requested."
            )

    if (
        budget is not None
        and estimated_cost is not None
        and estimated_cost > budget
    ):
        violations.append(
            f"Estimated trip cost ({estimated_cost}) exceeds the budget ({budget})."
        )

    floor_info = research_cost_floor(
        state.get("flight_data") or [],
        state.get("hotel_data") or [],
        origin=state.get("origin"),
        destination=state.get("destination"),
        travelers=travelers,
        duration_days=duration,
    )
    floor = floor_info.get("floor") or 0
    if estimated_cost is not None and floor > 0 and estimated_cost < floor:
        violations.append(
            f"Estimated trip cost ({estimated_cost}) is below the research-based "
            f"floor ({floor})."
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


def route_after_validation(state: TravelState):
    violations = state.get("constraint_violations", [])
    replan_count = state.get("replan_count", 0)

    if violations and replan_count < 2:
        return "replan"

    return "complete"


def replanner_node(state: TravelState) -> TravelState:
    duration = state.get("trip_duration_days")
    budget = state.get("budget")
    refinement = state.get("refinement_instruction")

    floor_info = research_cost_floor(
        state.get("flight_data") or [],
        state.get("hotel_data") or [],
        origin=state.get("origin"),
        destination=state.get("destination"),
        travelers=state.get("travelers"),
        duration_days=duration,
    )

    prompt = f"""
You are the replanning component of TripPilot.
The current itinerary failed validation.

CONSTRAINT VIOLATIONS:
{state.get("constraint_violations", [])}

CURRENT ITINERARY:
{state.get("itinerary", {})}

REFINEMENT INSTRUCTION:
{refinement or "None"}

USER REQUIREMENTS:
Origin: {state.get("origin")}
Destination: {state.get("destination")}
Travelers: {state.get("travelers")}
Budget: {budget}
Interests: {state.get("interests", [])}
Trip duration: {duration} days
Research cost floor (INR): {floor_info.get("floor")}

Create a revised itinerary.
- Fix every listed constraint violation.
- The itinerary MUST contain exactly {duration} days when duration is provided.
- Estimated cost must be at least the research cost floor and within budget
  when that is possible.
- Do not invent actual bookings.
- Apply the refinement instruction when present.

Return the complete revised itinerary.
"""

    revised = itinerary_llm.invoke(prompt)
    update = _apply_grounded_cost(state, revised)
    update["replan_count"] = state.get("replan_count", 0) + 1
    return update
