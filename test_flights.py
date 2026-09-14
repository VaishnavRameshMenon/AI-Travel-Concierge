import asyncio

from backend.app.tools.flights import search_flights


async def main():
    result = await search_flights(
        departure_iata="DEL",
        arrival_iata="NRT",
    )

    print("\n--- FLIGHT API TEST ---")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())