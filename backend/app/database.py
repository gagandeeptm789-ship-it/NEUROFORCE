"""
Database Engine & Session Management
Provides SQLAlchemy Base, engine, session factory, and FastAPI session dependencies.
Supports PostgreSQL (including Supabase) and SQLite for local development/testing.
"""

import logging
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import get_settings

logger = logging.getLogger("forwarded_seal.database")
settings = get_settings()

# Engine configuration
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,  # Automatically verify connection health before using
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency yielding a SQLAlchemy session.
    Automatically closes the session after request completion.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Idempotent database schema initializer.
    Creates all tables defined in Base subclasses if they do not already exist.
    """
    # Import models here to ensure they are registered with Base.metadata
    from app.models import admin, notice  # noqa: F401

    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")

