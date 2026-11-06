"""
Pytest Fixtures and Test Environment Setup
Provides an isolated file-backed SQLite database, test client, storage fixtures,
and authentication helpers without thread-locking issues.
"""

import os
import shutil
import tempfile
from typing import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure backend root is on sys.path
import sys
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

os.environ["ENVIRONMENT"] = "testing"
from app.core.config import get_settings
get_settings().ENVIRONMENT = "testing"
from app.core.security import create_access_token, get_password_hash
from app.database import Base, get_db
from app.main import app
from app.models.admin import Admin
from app.services.storage_service import LocalStorageService, get_storage_service


@pytest.fixture(scope="session")
def test_temp_dir():
    """Create a temporary directory for session database and storage."""
    temp_dir = tempfile.mkdtemp(prefix="seal_pytest_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope="session")
def test_engine(test_temp_dir):
    """Engine connected to a temporary SQLite file."""
    db_path = os.path.join(test_temp_dir, "test_seal.db")
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="session")
def TestingSession(test_engine):
    """Session factory for the test engine."""
    return sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(autouse=True)
def clean_tables(test_engine):
    """Ensure database tables exist and are cleaned between tests."""
    Base.metadata.create_all(bind=test_engine)
    yield
    with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())


@pytest.fixture
def db_session(TestingSession) -> Generator:
    """Provide a database session for test setup and verification."""
    session = TestingSession()
    yield session
    session.close()


@pytest.fixture
def temp_storage_dir(test_temp_dir):
    """Create a temporary directory for test file uploads."""
    storage_path = os.path.join(test_temp_dir, "uploads")
    os.makedirs(storage_path, exist_ok=True)
    yield storage_path
    shutil.rmtree(storage_path, ignore_errors=True)


@pytest.fixture
def test_storage(temp_storage_dir):
    """Provide a LocalStorageService instance pointing to temp directory."""
    return LocalStorageService(base_dir=temp_storage_dir)


@pytest.fixture
def client(TestingSession, test_storage) -> Generator:
    """FastAPI TestClient with overridden dependencies."""
    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    def override_get_storage():
        return test_storage

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_storage_service] = override_get_storage

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def test_admin(db_session) -> Admin:
    """Seed an active administrator in the database."""
    admin = Admin(
        email="testadmin@gmu.edu",
        full_name="Dr. Test Administrator",
        password_hash=get_password_hash("AdminSecret2026!"),
        role="super_admin",
        is_active=True,
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


@pytest.fixture
def inactive_admin(db_session) -> Admin:
    """Seed an inactive administrator in the database."""
    admin = Admin(
        email="inactive@gmu.edu",
        full_name="Deactivated Admin",
        password_hash=get_password_hash("AdminSecret2026!"),
        role="admin",
        is_active=False,
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


@pytest.fixture
def auth_headers(test_admin) -> dict:
    """Generate valid Bearer Authorization headers for test_admin."""
    token = create_access_token(
        data={
            "sub": str(test_admin.id),
            "email": test_admin.email,
            "role": test_admin.role,
        }
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_pdf_content() -> bytes:
    """Generate minimal valid PDF binary data."""
    return b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n%%EOF"


@pytest.fixture
def sample_png_content() -> bytes:
    """Generate minimal valid PNG binary data."""
    return b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"


@pytest.fixture
def sample_jpeg_content() -> bytes:
    """Generate minimal valid JPEG binary data."""
    return b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xd9"
