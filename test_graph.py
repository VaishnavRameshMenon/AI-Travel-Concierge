import asyncio

from backend.app.agent.graph import travel_graph


async def main():

    result = await travel_graph.ainvoke(
        {
            "user_query": (
    "I want to travel from Delhi to Tokyo "
    "from 2026-10-10 to 2026-10-16 for 7 days "
    "with 3 people. "
    "Our budget is 150000 rupees. "
    "We love anime, food and photography."
),
        }
    )

    print("\n========================================")
    print("TRIP REQUIREMENTS")
    print("========================================")

    print(
        "Origin:",
        result.get("origin"),
    )

    print(
        "Origin IATA:",
        result.get("origin_iata"),
    )

    print(
        "Destination:",
        result.get("destination"),
    )

    print(
        "Destination IATA:",
        result.get("destination_iata"),
    )

    print(
        "Start date:",
        result.get("start_date"),
    )

    print(
        "End date:",
        result.get("end_date"),
    )

    print(
        "Trip duration:",
        result.get("trip_duration_days"),
    )

    print(
        "Travelers:",
        result.get("travelers"),
    )

    print(
        "Budget:",
        result.get("budget"),
    )

    print(
        "Interests:",
        result.get("interests"),
    )

    print(
        "Required tools:",
        result.get("required_tools"),
    )


    print("\n========================================")
    print("FLIGHT DATA")
    print("========================================")

    flights = result.get(
        "flight_data",
        [],
    )

    if flights:

        for flight in flights:
            print(
                "Flight:",
                flight.get("flight_number"),
            )

            print(
                "Airline:",
                flight.get("airline"),
            )

            print(
                "Departure:",
                flight.get("departure"),
                flight.get("departure_iata"),
            )

            print(
                "Arrival:",
                flight.get("arrival"),
                flight.get("arrival_iata"),
            )

            print(
                "Departure time:",
                flight.get("departure_time"),
            )

            print(
                "Arrival time:",
                flight.get("arrival_time"),
            )

            print(
                "Status:",
                flight.get("status"),
            )

            print("----------------------------------------")

    else:
        print("No flight data returned.")


    print("\n========================================")
    print("WEATHER")
    print("========================================")

    weather = result.get(
        "weather_data"
    )

    if weather:
        print(
            "Current:",
            weather.get("current"),
        )
    else:
        print(
            "No weather data returned."
        )


    print("\n========================================")
    print("ITINERARY")
    print("========================================")

    itinerary = result.get(
        "itinerary"
    )

    if itinerary:

        print(
            "Title:",
            itinerary.get("title"),
        )

        print(
            "Summary:",
            itinerary.get("summary"),
        )

        print(
            "Estimated Cost:",
            itinerary.get(
                "estimated_cost"
            ),
        )

        print("\nDays:")

        for day in itinerary.get(
            "days",
            [],
        ):
            print(day)

    else:
        print(
            "No itinerary generated."
        )


    print("\n========================================")
    print("VALIDATION")
    print("========================================")

    print(
        "Constraint violations:",
        result.get(
            "constraint_violations"
        ),
    )

    print(
        "Replan count:",
        result.get(
            "replan_count"
        ),
    )

    print(
        "Final action:",
        result.get(
            "next_action"
        ),
    )

    print(
        "Error:",
        result.get(
            "error"
        ),
    )


if __name__ == "__main__":
    asyncio.run(main())