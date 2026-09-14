from backend.app.database.database import Base, engine
from backend.app.database.models import Trip


def init_db():
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")


if __name__ == "__main__":
    init_db()