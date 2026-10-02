"""Database initialisation – safe for existing Supabase/PostgreSQL databases.

``create_all(checkfirst=True)`` (the SQLAlchemy default) creates the table if it
does not exist.  For an existing ``trips`` table the new nullable columns
(user_query, origin, flight_data, hotel_data, attraction_data) are added via
explicit ALTER TABLE statements so that no data is lost and no migration tool is
needed.
"""

from sqlalchemy import inspect, text

from backend.app.database.database import Base, engine
from backend.app.database.models import Trip  # noqa: F401 – registers the model


_NEW_NULLABLE_COLUMNS: list[tuple[str, str]] = [
    ("user_query",      "TEXT"),
    ("origin",          "VARCHAR(255)"),
    ("flight_data",     "JSONB"),
    ("hotel_data",      "JSONB"),
    ("attraction_data", "JSONB"),
]


def _add_missing_columns() -> None:
    """Idempotently add any new columns that are not yet present in the table."""
    inspector = inspect(engine)

    # Table may not exist yet – that case is handled by create_all below.
    if not inspector.has_table("trips"):
        return

    existing = {col["name"] for col in inspector.get_columns("trips")}
    missing = [
        (col, dtype)
        for col, dtype in _NEW_NULLABLE_COLUMNS
        if col not in existing
    ]

    if not missing:
        return

    with engine.begin() as conn:
        for col, dtype in missing:
            conn.execute(
                text(f'ALTER TABLE trips ADD COLUMN IF NOT EXISTS "{col}" {dtype}')
            )


def init_db() -> None:
    if engine is None:
        raise RuntimeError("DATABASE_URL is not configured.")

    # Add missing columns to an already-existing table before create_all
    # so that SQLAlchemy's metadata stays in sync.
    _add_missing_columns()

    # Create the table if it does not exist yet (no-op when it already does).
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
