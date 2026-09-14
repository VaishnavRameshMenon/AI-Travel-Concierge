import asyncio

from backend.app.tools.attractions import search_attractions


async def main():
    result = await search_attractions(
        latitude=35.7,
        longitude=139.75,
        interests=["anime", "food", "photography"],
    )

    print(result)


if __name__ == "__main__":
    asyncio.run(main())