"""
Authentication Router
Endpoints for administrator login, profile retrieval, and controlled registration.
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import create_access_token
from app.database import get_db
from app.models.admin import Admin
from app.schemas.admin import AdminCreate, AdminLogin, AdminResponse, TokenResponse
from app.services.auth_service import (
    authenticate_admin,
    get_current_active_admin,
    register_admin,
)

logger = logging.getLogger("forwarded_seal.auth_router")
settings = get_settings()

router = APIRouter(prefix="/admin", tags=["Administrator Authentication"])


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Administrator Login",
    description="Authenticate an administrator with email and password to receive a JWT access token.",
)
def login_admin(
    credentials: AdminLogin,
    db: Session = Depends(get_db),
):
    """Authenticate administrator and return Bearer token."""
    admin = authenticate_admin(
        db=db,
        email=credentials.email,
        password=credentials.password,
    )
    if not admin:
        # Generic error message to prevent account enumeration
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Issue JWT token
    access_token = create_access_token(
        data={
            "sub": str(admin.id),
            "email": admin.email,
            "role": admin.role,
        }
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        admin=AdminResponse.model_validate(admin),
    )


@router.get(
    "/me",
    response_model=AdminResponse,
    summary="Current Admin Profile",
    description="Retrieve the profile of the currently authenticated administrator.",
)
def get_admin_profile(
    current_admin: Admin = Depends(get_current_active_admin),
):
    """Return profile of currently logged-in administrator."""
    return AdminResponse.model_validate(current_admin)


@router.post(
    "/register",
    response_model=AdminResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register Administrator (Protected)",
    description=(
        "Controlled administrator creation. Requires the 'X-Admin-Registration-Secret' "
        "header matching the server configuration."
    ),
)
def register_new_admin(
    admin_in: AdminCreate,
    x_admin_registration_secret: Optional[str] = Header(
        None,
        alias="X-Admin-Registration-Secret",
        description="Bootstrap secret token required for admin onboarding",
    ),
    db: Session = Depends(get_db),
):
    """
    Controlled registration endpoint.
    Guards against public unauthorized administrator creation.
    """
    expected_secret = settings.ADMIN_REGISTRATION_SECRET
    if not x_admin_registration_secret or x_admin_registration_secret != expected_secret:
        logger.warning("Unauthorized attempt to access /admin/register endpoint.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator registration is restricted. Provide valid authorization.",
        )

    new_admin = register_admin(db=db, admin_in=admin_in)
    return AdminResponse.model_validate(new_admin)

