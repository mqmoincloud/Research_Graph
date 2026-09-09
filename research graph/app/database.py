"""Database engine, session and Base.

Nothing in the LangGraph part of this project touches the database. It exists
only for the accounts: who is allowed to POST /api/run.
"""

from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import config

engine = create_engine(
    config.db_url,
    # SQLite refuses to use one connection from two threads unless this is off.
    # It has to be off here: uvicorn serves requests on a thread pool, so the
    # thread that opened a connection is rarely the one that uses it next.
    connect_args={"check_same_thread": False},
)

localSession = sessionmaker(bind=engine)

Base = declarative_base()


def now():
    return datetime.now()


def get_db():

    db = localSession()
    try:
        yield db
    finally:
        db.close()
