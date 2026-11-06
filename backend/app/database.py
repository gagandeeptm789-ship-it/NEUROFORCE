"""
Database Engine & Session Management
Provides SQLAlchemy Base, engine, session factory, and FastAPI session dependencies.
Supports PostgreSQL (including Supabase) and SQLite for local development/testing.
"""

import logging
import os
from typing import Generator
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect
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
    Apply versioned schema migrations, including updates to existing tables.
    """
    # Import models here to ensure they are registered with Base.metadata
    from app.models import admin, notice  # noqa: F401

    logger.info("Applying database migrations...")
    config = Config(os.path.join(os.path.dirname(os.path.dirname(__file__)), "alembic.ini"))
    config.set_main_option("sqlalchemy.url", settings.DATABASE_URL.replace("%", "%%"))

    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    if {"admins", "notices"}.issubset(existing_tables) and "alembic_version" not in existing_tables:
        expected_columns = {
            "admins": {
                "id", "full_name", "email", "password_hash", "role",
                "is_active", "created_at", "updated_at",
            },
            "notices": {
                "id", "notice_id", "title", "description", "category",
                "original_filename", "stored_file_path", "mime_type", "file_size",
                "issuer_admin_id", "publication_status", "created_at", "updated_at",
                "sha256_hash", "digital_signature", "signing_key_id",
                "signed_metadata", "revoked_at",
            },
        }
        for table_name, required_columns in expected_columns.items():
            actual_columns = {column["name"] for column in inspector.get_columns(table_name)}
            missing_columns = required_columns - actual_columns
            if missing_columns:
                raise RuntimeError(
                    f"Cannot automatically migrate legacy table '{table_name}'; "
                    f"missing required columns: {', '.join(sorted(missing_columns))}."
                )
        notice_columns = {
            column["name"] for column in inspector.get_columns("notices")
        }
        secure_publishing_columns = {
            "hash_algorithm",
            "signature_algorithm",
            "metadata_version",
            "signed_at",
            "distribution_status",
            "qr_code_path",
            "verification_url",
            "watermarked_file_path",
            "published_file_path",
            "watermark_version",
            "watermark_reference",
            "publication_timestamp",
        }
        existing_secure_columns = notice_columns & secure_publishing_columns
        if existing_secure_columns and existing_secure_columns != secure_publishing_columns:
            missing_columns = secure_publishing_columns - existing_secure_columns
            raise RuntimeError(
                "Cannot automatically migrate a partially upgraded legacy notices table; "
                f"missing columns: {', '.join(sorted(missing_columns))}."
            )
        baseline_revision = (
            "002_crypto_publishing"
            if existing_secure_columns
            else "001_initial_schema"
        )
        logger.info(
            "Recognized an existing pre-Alembic database; recording baseline revision %s.",
            baseline_revision,
        )
        command.stamp(config, baseline_revision)

    command.upgrade(config, "head")
    logger.info("Database migrations completed successfully.")
