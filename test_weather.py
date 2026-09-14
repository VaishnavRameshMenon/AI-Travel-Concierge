import asyncio

from backend.app.tools.weather import geocode_destination


async def main():
    result = await geocode_destination("Tokyo")

    print(result)


if __name__ == "__main__":
    asyncio.run(main())