"""
Authentication Service
Handles administrator authentication, registration, password validation,
and FastAPI security dependencies.
"""

import logging
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import (
    decode_access_token,
    get_password_hash,
    security_bearer,
    validate_password_strength,
    verify_password,
)
from app.database import get_db
from app.models.admin import Admin
from app.schemas.admin import AdminCreate, ALLOWED_ADMIN_ROLES

logger = logging.getLogger("forwarded_seal.auth")
settings = get_settings()


def get_admin_by_email(db: Session, email: str) -> Optional[Admin]:
    """Retrieve an administrator by normalized lowercase email."""
    if not email:
        return None
    return db.query(Admin).filter(Admin.email == email.strip().lower()).first()


def get_admin_by_id(db: Session, admin_id: str) -> Optional[Admin]:
    """Retrieve an administrator by primary key ID."""
    if not admin_id:
        return None
    return db.query(Admin).filter(Admin.id == admin_id).first()


def authenticate_admin(db: Session, email: str, password: str) -> Optional[Admin]:
    """
    Authenticate an administrator using email and plaintext password.
    Returns the Admin entity if valid, raises HTTPException(403) if inactive,
    or returns None if credentials do not match.
    """
    admin = get_admin_by_email(db, email)
    if not admin:
        logger.warning("Authentication failed: User with email '%s' not found.", email)
        return None

    if not verify_password(password, admin.password_hash):
        logger.warning("Authentication failed: Invalid password for email '%s'.", email)
        return None

    if not admin.is_active:
        logger.warning("Authentication blocked: Admin account '%s' is inactive.", email)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive. Please contact the system administrator.",
        )

    logger.info("Admin '%s' (%s) successfully authenticated.", admin.email, admin.id)
    return admin


def register_admin(db: Session, admin_in: AdminCreate) -> Admin:
    """
    Create a new administrator record.
    Enforces email uniqueness and password complexity.
    """
    normalized_email = admin_in.email.strip().lower()
    existing = get_admin_by_email(db, normalized_email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An administrator with this email address already exists.",
        )

    # Validate password complexity
    valid_pwd, reason = validate_password_strength(admin_in.password)
    if not valid_pwd:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=reason,
        )

    normalized_role = (admin_in.role or "admin").strip().lower()
    if normalized_role not in ALLOWED_ADMIN_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role must be one of: {', '.join(sorted(ALLOWED_ADMIN_ROLES))}",
        )

    password_hash = get_password_hash(admin_in.password)
    new_admin = Admin(
        full_name=admin_in.full_name.strip(),
        email=normalized_email,
        password_hash=password_hash,
        role=normalized_role,
        is_active=True,
    )
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)
    logger.info("Created new administrator: %s (%s)", new_admin.email, new_admin.id)
    return new_admin


def ensure_default_admin(
    db: Session,
    email: str,
    full_name: str,
    password: str,
    role: str = "institutional_admin",
) -> Admin:
    """Create the configured development admin once without changing existing credentials."""
    existing = get_admin_by_email(db, email)
    if existing:
        if existing.role != role:
            existing.role = role
            db.commit()
            db.refresh(existing)
        logger.info("Default administrator '%s' already exists; leaving its credentials unchanged.", existing.email)
        return existing

    return register_admin(
        db,
        AdminCreate(
            email=email,
            full_name=full_name,
            password=password,
            role=role,
        ),
    )


# ==============================================================================
# FastAPI Route Dependencies
# ==============================================================================

def get_current_admin(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: Session = Depends(get_db),
) -> Admin:
    """
    Dependency to extract and validate the JWT Bearer token from request headers.
    Returns the Admin model instance.
    """
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(credentials.credentials)
    admin_id = payload.get("sub")
    if not admin_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    admin = get_admin_by_id(db, admin_id)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Administrator account not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return admin


def get_current_active_admin(
    current_admin: Admin = Depends(get_current_admin),
) -> Admin:
    """Dependency verifying that the authenticated administrator is active."""
    if not current_admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator account is inactive.",
        )
    return current_admin
