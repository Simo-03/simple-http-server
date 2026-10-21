from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from dotenv import load_dotenv

import os

load_dotenv()



DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL is None:
    raise RuntimeError("DATABASE_URL environment variable is not set")


# an Engine, used by the a Session to connect to the DB
engine = create_engine(DATABASE_URL, echo=True)

# a session factory, used to create a fresh session for each request
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
    )


class Base(DeclarativeBase):
    pass

def get_db():
    with SessionLocal() as session:
        yield session

