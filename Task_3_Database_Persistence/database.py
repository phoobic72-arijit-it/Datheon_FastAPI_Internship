"""Async SQLite engine and one database session per request."""

from pathlib import Path

from sqlalchemy import event
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

DATA_DIRECTORY = Path(__file__).resolve().parent / "data"
DATA_DIRECTORY.mkdir(exist_ok=True)
DATABASE_PATH = DATA_DIRECTORY / "users_notes.db"
DATABASE_URL = f"sqlite+aiosqlite:///{DATABASE_PATH.as_posix()}"

engine = create_async_engine(DATABASE_URL, connect_args={"timeout": 10})
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


@event.listens_for(engine.sync_engine, "connect")
def configure_sqlite(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=10000")
    cursor.close()


async def get_db():
    async with SessionLocal() as session:
        yield session
