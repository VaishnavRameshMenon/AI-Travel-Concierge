from sqlalchemy import text

from backend.app.database.database import engine
from backend.app.database.init_db import init_db


def main():
    print("\n--- DATABASE CONNECTION TEST ---")

    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("PostgreSQL connection: SUCCESS")
            print("Test result:", result.scalar())

        init_db()

        print("Database setup: SUCCESS")

    except Exception as e:
        print("Database connection: FAILED")
        print("Error:", e)


if __name__ == "__main__":
    main()