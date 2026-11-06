"""
Application Configuration Module
Loads environment variables safely and defines system-wide settings.
"""

import os
from functools import lru_cache
from typing import List
from dotenv import load_dotenv

# Locate and load the .env file from the backend directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
env_path = os.path.join(BASE_DIR, ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    load_dotenv()


class Settings:
    """Application runtime settings with environment overrides."""

    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "The Forwarded Seal")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() in ("true", "1", "yes")
    API_V1_PREFIX: str = os.getenv("API_V1_PREFIX", "/api")
    AUTO_CREATE_DEFAULT_ADMIN: bool = os.getenv(
        "AUTO_CREATE_DEFAULT_ADMIN",
        "true" if ENVIRONMENT.lower() == "development" else "false",
    ).lower() in ("true", "1", "yes")
    DEFAULT_ADMIN_EMAIL: str = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@gmu.edu")
    DEFAULT_ADMIN_PASSWORD: str = os.getenv("DEFAULT_ADMIN_PASSWORD", "Gmu@12345!")
    DEFAULT_ADMIN_NAME: str = os.getenv("DEFAULT_ADMIN_NAME", "University Registrar")
    DEFAULT_ADMIN_ROLE: str = os.getenv("DEFAULT_ADMIN_ROLE", "institutional_admin")

    # Security & JWT
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY",
        "insecure-dev-secret-key-change-this-in-production-neuroforce-phase2",
    )
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

    # Admin Registration Secret Token
    ADMIN_REGISTRATION_SECRET: str = os.getenv(
        "ADMIN_REGISTRATION_SECRET", "seal-admin-bootstrap-secret-change-in-prod"
    )

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./forwarded_seal.db")

    # Storage
    STORAGE_PROVIDER: str = os.getenv("STORAGE_PROVIDER", "local").lower()
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
    MAX_UPLOAD_SIZE_BYTES: int = int(os.getenv("MAX_UPLOAD_SIZE_BYTES", str(10 * 1024 * 1024)))

    # Notice ID Pattern
    NOTICE_ID_PREFIX: str = os.getenv("NOTICE_ID_PREFIX", "FS")
    INSTITUTION_CODE: str = os.getenv("INSTITUTION_CODE", "GMU")

    # Phase 3: Cryptography & Key Management
    KEYS_DIR: str = os.getenv("KEYS_DIR", "keys")
    SIGNING_KEY_ID: str = os.getenv("SIGNING_KEY_ID", "key-GMU-2026-v1-ed25519")

    # Phase 4: Public Verification URL & Publishing Artifact Directories
    PUBLIC_VERIFICATION_BASE_URL: str = os.getenv(
        "PUBLIC_VERIFICATION_BASE_URL", "http://localhost:3000/verify"
    )
    QR_DIR: str = os.getenv("QR_DIR", "uploads/qr_codes")
    WATERMARK_DIR: str = os.getenv("WATERMARK_DIR", "uploads/watermarked")
    PUBLISHED_DIR: str = os.getenv("PUBLISHED_DIR", "uploads/published")

    # CORS Origins
    _raw_cors: str = os.getenv(
        "ALLOWED_CORS_ORIGINS",
        "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173",
    )

    @property
    def ALLOWED_CORS_ORIGINS(self) -> List[str]:
        if not self._raw_cors:
            return ["*"]
        return [origin.strip() for origin in self._raw_cors.split(",") if origin.strip()]

    # Future Supabase storage support
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    SUPABASE_BUCKET_NAME: str = os.getenv("SUPABASE_BUCKET_NAME", "notices")


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()
