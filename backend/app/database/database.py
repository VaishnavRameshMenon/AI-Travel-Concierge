import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Keep imports and health checks available when PostgreSQL is temporarily
# unavailable. Database-dependent endpoints report a clear service error.
engine = (
    create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=300)
    if DATABASE_URL
    else None
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def is_database_configured() -> bool:
    return engine is not None
