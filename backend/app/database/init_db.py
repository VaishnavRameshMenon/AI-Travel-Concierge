from backend.app.database.database import Base, engine
from backend.app.database.models import Trip


def init_db():
    if engine is None:
        raise RuntimeError("DATABASE_URL is not configured.")
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
