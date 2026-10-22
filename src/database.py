import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()


DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL is None:
    raise RuntimeError("DATABASE_URL environment variable is not set")


# Shared engine and connection pool used by database sessions.
engine = create_engine(DATABASE_URL, echo=True)

# Session factory used to create a fresh session for each request.
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


def get_db():
    # Close the session and return any borrowed connection to the pool,
    # including when request handling raises an exception.
    with SessionLocal() as session:
        yield session
