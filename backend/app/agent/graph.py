from langgraph.graph import StateGraph, START, END

from backend.app.agent.state import TravelState

from backend.app.agent.nodes import (
    planner_node,
    research_node,
    geocoder_node,
    weather_node,
    attractions_node,
    flights_node,
    hotels_node,
    research_complete_node,
    itinerary_node,
    constraint_checker_node,
    replanner_node,
    route_research,
    route_after_validation,
)


# ============================================================
# CREATE GRAPH
# ============================================================

graph = StateGraph(TravelState)


# ============================================================
# NODES
# ============================================================

graph.add_node("planner", planner_node)
graph.add_node("research", research_node)
graph.add_node("geocoder", geocoder_node)
graph.add_node("weather", weather_node)
graph.add_node("attractions", attractions_node)
graph.add_node("flights", flights_node)
graph.add_node("hotels", hotels_node)
graph.add_node("research_complete", research_complete_node)
graph.add_node("itinerary", itinerary_node)
graph.add_node("constraint_checker", constraint_checker_node)
graph.add_node("replanner", replanner_node)


# ============================================================
# MAIN FLOW
# ============================================================

graph.add_edge(START, "planner")
graph.add_edge("planner", "research")
graph.add_edge("research", "geocoder")


# ============================================================
# PARALLEL RESEARCH
# ============================================================

graph.add_conditional_edges(
    "geocoder",
    route_research,
    {
        "weather": "weather",
        "attractions": "attractions",
        "flights": "flights",
        "hotels": "hotels",
        "end": END,
    },
)

graph.add_edge("weather", "research_complete")
graph.add_edge("attractions", "research_complete")
graph.add_edge("flights", "research_complete")
graph.add_edge("hotels", "research_complete")


# ============================================================
# ITINERARY
# ============================================================

graph.add_edge("research_complete", "itinerary")
graph.add_edge("itinerary", "constraint_checker")


# ============================================================
# VALIDATION
# ============================================================

graph.add_conditional_edges(
    "constraint_checker",
    route_after_validation,
    {
        "complete": END,
        "replan": "replanner",
    },
)


# ============================================================
# REPLANNING
# ============================================================

graph.add_edge("replanner", "constraint_checker")


# ============================================================
# COMPILE
# ============================================================

travel_graph = graph.compile()