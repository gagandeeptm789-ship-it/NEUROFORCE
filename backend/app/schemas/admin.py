"""
Admin Schemas
Defines request and response validation contracts for administrator accounts.
Enforces that sensitive data like password_hash is never exposed.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

ALLOWED_ADMIN_ROLES = {"super_admin", "admin", "exam_cell"}


class AdminBase(BaseModel):
    """Base administrator attributes."""
    full_name: str = Field(..., min_length=2, max_length=100, description="Full name of administrator")
    email: EmailStr = Field(..., description="Institutional email address")
    role: str = Field("admin", min_length=2, max_length=50, description="Role: super_admin, admin, exam_cell, etc.")

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str) -> str:
        role = value.strip().lower()
        if role not in ALLOWED_ADMIN_ROLES:
            raise ValueError(f"Role must be one of: {', '.join(sorted(ALLOWED_ADMIN_ROLES))}")
        return role


class AdminCreate(AdminBase):
    """Payload for registering a new administrator."""
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Strong password meeting university security policy",
    )


class AdminLogin(BaseModel):
    """Credentials required for administrator authentication."""
    email: EmailStr = Field(..., description="Registered administrator email")
    password: str = Field(..., min_length=1, description="Account password")


class AdminResponse(BaseModel):
    """Safe public representation of an administrator (no password hashes)."""
    id: str
    full_name: str
    email: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """JWT authentication response payload for Phase 1 frontend."""
    access_token: str
    token_type: str = "bearer"
    admin: AdminResponse


class AdminUpdate(BaseModel):
    """Attributes that can be updated for an administrator."""
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    role: Optional[str] = Field(None, min_length=2, max_length=50)
    is_active: Optional[bool] = None

