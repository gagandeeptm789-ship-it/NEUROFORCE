"""
Authentication & Authorization Tests
Verifies admin login, token validation, password security, registration protection, and access control.
"""

from datetime import timedelta
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.core.config import get_settings
from app.core.security import create_access_token
from app.routers.auth import get_admin_profile, login_admin, register_new_admin
from app.schemas.admin import AdminCreate, AdminLogin
from app.services.auth_service import get_current_active_admin, get_current_admin

settings = get_settings()


def test_login_success(db_session, test_admin):
    """Test successful administrator login returning JWT and safe admin profile."""
    credentials = AdminLogin(email="testadmin@gmu.edu", password="AdminSecret2026!")
    response = login_admin(credentials=credentials, db=db_session)

    assert response.access_token is not None
    assert response.token_type == "bearer"
    assert response.admin.email == "testadmin@gmu.edu"
    assert response.admin.full_name == "Dr. Test Administrator"
    assert response.admin.role == "super_admin"
    assert not hasattr(response.admin, "password_hash")


def test_login_incorrect_password(db_session, test_admin):
    """Test login failure on incorrect password (HTTP 401)."""
    credentials = AdminLogin(email="testadmin@gmu.edu", password="WrongPassword999!")
    with pytest.raises(HTTPException) as exc_info:
        login_admin(credentials=credentials, db=db_session)

    assert exc_info.value.status_code == 401
    assert "Invalid email or password" in exc_info.value.detail


def test_login_nonexistent_email(db_session):
    """Test login failure on unmapped email address (HTTP 401, avoids user enumeration)."""
    credentials = AdminLogin(email="doesnotexist@gmu.edu", password="AnyPassword123!")
    with pytest.raises(HTTPException) as exc_info:
        login_admin(credentials=credentials, db=db_session)

    assert exc_info.value.status_code == 401
    assert "Invalid email or password" in exc_info.value.detail


def test_login_inactive_admin(db_session, inactive_admin):
    """Test that deactivated administrator accounts cannot log in (HTTP 403)."""
    credentials = AdminLogin(email="inactive@gmu.edu", password="AdminSecret2026!")
    with pytest.raises(HTTPException) as exc_info:
        login_admin(credentials=credentials, db=db_session)

    assert exc_info.value.status_code == 403
    assert "inactive" in exc_info.value.detail.lower()


def test_get_current_admin_me_success(test_admin):
    """Test profile retrieval for authenticated administrator."""
    profile = get_admin_profile(current_admin=test_admin)
    assert profile.id == str(test_admin.id)
    assert profile.email == test_admin.email
    assert profile.role == test_admin.role
    assert not hasattr(profile, "password_hash")


def test_get_current_admin_dependency_valid_token(db_session, test_admin):
    """Test security dependency extracts Admin from valid JWT Bearer credentials."""
    token = create_access_token(
        data={"sub": str(test_admin.id), "email": test_admin.email, "role": test_admin.role}
    )
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    admin = get_current_admin(credentials=creds, db=db_session)
    assert admin.id == test_admin.id
    assert admin.email == test_admin.email


def test_get_current_admin_missing_token(db_session):
    """Test security dependency rejects request without credentials (HTTP 401)."""
    with pytest.raises(HTTPException) as exc_info:
        get_current_admin(credentials=None, db=db_session)
    assert exc_info.value.status_code == 401


def test_get_current_admin_invalid_jwt(db_session):
    """Test security dependency rejects tampered or malformed JWT (HTTP 401)."""
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="tampered.invalid.token")
    with pytest.raises(HTTPException) as exc_info:
        get_current_admin(credentials=creds, db=db_session)
    assert exc_info.value.status_code == 401


def test_get_current_admin_expired_jwt(db_session, test_admin):
    """Test that expired JWT is rejected with HTTP 401."""
    expired_token = create_access_token(
        data={"sub": str(test_admin.id)},
        expires_delta=timedelta(seconds=-10),
    )
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=expired_token)
    with pytest.raises(HTTPException) as exc_info:
        get_current_admin(credentials=creds, db=db_session)
    assert exc_info.value.status_code == 401
    assert "expired" in exc_info.value.detail.lower()


def test_inactive_admin_blocked_by_active_dependency(inactive_admin):
    """Test get_current_active_admin blocks inactive accounts (HTTP 403)."""
    with pytest.raises(HTTPException) as exc_info:
        get_current_active_admin(current_admin=inactive_admin)
    assert exc_info.value.status_code == 403


def test_admin_registration_protected_without_secret(db_session):
    """Test public registration without authorization secret is forbidden (HTTP 403)."""
    payload = AdminCreate(
        email="newadmin@gmu.edu",
        full_name="New Admin",
        password="SecurePassword123!",
        role="admin",
    )
    with pytest.raises(HTTPException) as exc_info:
        register_new_admin(admin_in=payload, x_admin_registration_secret=None, db=db_session)
    assert exc_info.value.status_code == 403


def test_admin_registration_with_valid_secret(db_session):
    """Test controlled registration with valid X-Admin-Registration-Secret header."""
    payload = AdminCreate(
        email="newadmin@gmu.edu",
        full_name="New Admin User",
        password="SecurePassword2026!",
        role="admin",
    )
    response = register_new_admin(
        admin_in=payload,
        x_admin_registration_secret=settings.ADMIN_REGISTRATION_SECRET,
        db=db_session,
    )
    assert response.email == "newadmin@gmu.edu"
    assert response.full_name == "New Admin User"
    assert not hasattr(response, "password_hash")


def test_admin_registration_weak_password_rejected(db_session):
    """Test passwords failing university complexity rules are rejected (HTTP 400)."""
    payload = AdminCreate(
        email="weakpass@gmu.edu",
        full_name="Weak Pass User",
        password="simplepassword",
        role="admin",
    )
    with pytest.raises(HTTPException) as exc_info:
        register_new_admin(
            admin_in=payload,
            x_admin_registration_secret=settings.ADMIN_REGISTRATION_SECRET,
            db=db_session,
        )
    assert exc_info.value.status_code == 400
    assert "password" in exc_info.value.detail.lower()


def test_admin_registration_duplicate_email(db_session, test_admin):
    """Test registering duplicate email is rejected (HTTP 400)."""
    payload = AdminCreate(
        email=test_admin.email,
        full_name="Duplicate User",
        password="SecurePassword2026!",
        role="admin",
    )
    with pytest.raises(HTTPException) as exc_info:
        register_new_admin(
            admin_in=payload,
            x_admin_registration_secret=settings.ADMIN_REGISTRATION_SECRET,
            db=db_session,
        )
    assert exc_info.value.status_code == 400
    assert "already exists" in exc_info.value.detail.lower()
