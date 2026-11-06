"""
Notice Management & File Upload Tests
Verifies official notice creation, file type validation (extension & magic bytes),
file size constraints, unique Notice ID generation, retrieval, status updates, and document streaming.
"""

import io
import pytest
from fastapi import HTTPException, UploadFile

from app.core import config
from app.routers.notices import (
    create_new_notice,
    download_notice_file,
    get_notice,
    get_notices,
    patch_notice_status,
)
from app.schemas.notice import NoticeStatusUpdate


def create_mock_upload_file(content: bytes, filename: str, content_type: str) -> UploadFile:
    """Helper to construct a FastAPI UploadFile from bytes."""
    file_io = io.BytesIO(content)
    return UploadFile(file=file_io, filename=filename, headers={"content-type": content_type})


def test_create_notice_pdf_success(db_session, test_admin, test_storage, sample_pdf_content, monkeypatch):
    """Test successful creation of a notice with valid PDF upload."""
    from app.services import notice_service
    monkeypatch.setattr(notice_service, "get_storage_service", lambda: test_storage)

    upload = create_mock_upload_file(sample_pdf_content, "exam_schedule.pdf", "application/pdf")
    notice_res = create_new_notice(
        title="Fall 2026 Final Examination Schedule",
        description="Comprehensive schedule for all undergraduate courses.",
        category="Examination",
        publication_status="published",
        file=upload,
        current_admin=test_admin,
        db=db_session,
    )

    assert notice_res.title == "Fall 2026 Final Examination Schedule"
    assert notice_res.category == "Examination"
    assert notice_res.publication_status == "published"
    assert notice_res.original_filename == "exam_schedule.pdf"
    assert notice_res.mime_type == "application/pdf"
    assert notice_res.file_size == len(sample_pdf_content)
    assert notice_res.issuer_admin_id == str(test_admin.id)

    # Validate Notice ID structure: FS-GMU-2026-A8F29C
    notice_id = notice_res.notice_id
    assert notice_id.startswith("FS-GMU-")
    parts = notice_id.split("-")
    assert len(parts) == 4
    assert len(parts[3]) == 6  # 6-char random hex


def test_create_notice_png_image_success(db_session, test_admin, test_storage, sample_png_content, monkeypatch):
    """Test successful creation of a notice with genuine PNG image."""
    from app.services import notice_service
    monkeypatch.setattr(notice_service, "get_storage_service", lambda: test_storage)

    upload = create_mock_upload_file(sample_png_content, "campus_poster.png", "image/png")
    notice_res = create_new_notice(
        title="Annual Science Fair 2026",
        description="Poster announcement.",
        category="Events",
        publication_status="published",
        file=upload,
        current_admin=test_admin,
        db=db_session,
    )

    assert notice_res.mime_type == "image/png"
    assert notice_res.original_filename == "campus_poster.png"
    assert notice_res.notice_id.startswith("FS-GMU-")


def test_create_notice_jpeg_image_success(db_session, test_admin, test_storage, sample_jpeg_content, monkeypatch):
    """Test successful creation of a notice with genuine JPEG image."""
    from app.services import notice_service
    monkeypatch.setattr(notice_service, "get_storage_service", lambda: test_storage)

    upload = create_mock_upload_file(sample_jpeg_content, "circular.jpg", "image/jpeg")
    notice_res = create_new_notice(
        title="Convocation Guidelines",
        description=None,
        category="Academic",
        publication_status="published",
        file=upload,
        current_admin=test_admin,
        db=db_session,
    )

    assert notice_res.mime_type == "image/jpeg"
    assert notice_res.notice_id.startswith("FS-GMU-")


def test_create_notice_invalid_file_extension(db_session, test_admin):
    """Test rejection of disallowed file extensions (e.g., .exe, .sh)."""
    upload = create_mock_upload_file(b"MZ\x90\x00executable", "malware.exe", "application/x-msdownload")
    with pytest.raises(HTTPException) as exc_info:
        create_new_notice(
            title="Invalid File Notice",
            description=None,
            category="General",
            publication_status="published",
            file=upload,
            current_admin=test_admin,
            db=db_session,
        )
    assert exc_info.value.status_code == 400
    assert "unsupported file type" in exc_info.value.detail.lower()


def test_create_notice_spoofed_file_magic_bytes(db_session, test_admin):
    """
    Test deep binary inspection: A file named 'important.pdf' containing shell script
    must be rejected because its magic bytes do not begin with %PDF-.
    """
    fake_pdf = b"echo 'Malicious disguised payload pretending to be PDF'"
    upload = create_mock_upload_file(fake_pdf, "important.pdf", "application/pdf")
    with pytest.raises(HTTPException) as exc_info:
        create_new_notice(
            title="Spoofed PDF Document",
            description=None,
            category="General",
            publication_status="published",
            file=upload,
            current_admin=test_admin,
            db=db_session,
        )
    assert exc_info.value.status_code == 400
    assert "does not match genuine" in exc_info.value.detail.lower()


def test_create_notice_empty_file(db_session, test_admin):
    """Test rejection of empty 0-byte file upload."""
    upload = create_mock_upload_file(b"", "empty.pdf", "application/pdf")
    with pytest.raises(HTTPException) as exc_info:
        create_new_notice(
            title="Empty Document Notice",
            description=None,
            category="General",
            publication_status="published",
            file=upload,
            current_admin=test_admin,
            db=db_session,
        )
    assert exc_info.value.status_code == 400
    assert "empty" in exc_info.value.detail.lower()


def test_create_notice_oversized_file(db_session, test_admin, monkeypatch):
    """Test rejection when file exceeds configured MAX_UPLOAD_SIZE_BYTES."""
    monkeypatch.setattr(config.get_settings(), "MAX_UPLOAD_SIZE_BYTES", 100)

    oversized_data = b"%PDF-" + b"A" * 200
    upload = create_mock_upload_file(oversized_data, "too_large.pdf", "application/pdf")
    with pytest.raises(HTTPException) as exc_info:
        create_new_notice(
            title="Oversized Document",
            description=None,
            category="General",
            publication_status="published",
            file=upload,
            current_admin=test_admin,
            db=db_session,
        )
    assert exc_info.value.status_code == 400
    assert "exceeds maximum allowed size" in exc_info.value.detail.lower()


def test_get_notice_by_id_and_not_found(db_session, test_admin, test_storage, sample_pdf_content, monkeypatch):
    """Test retrieving notice by Notice ID and handling 404 for nonexistent Notice ID."""
    from app.services import notice_service
    monkeypatch.setattr(notice_service, "get_storage_service", lambda: test_storage)

    upload = create_mock_upload_file(sample_pdf_content, "working_hours.pdf", "application/pdf")
    created = create_new_notice(
        title="Library Working Hours Update",
        description="Extended hours during exam week.",
        category="General",
        publication_status="published",
        file=upload,
        current_admin=test_admin,
        db=db_session,
    )
    notice_id = created.notice_id

    # Successful retrieval
    fetched = get_notice(notice_id=notice_id, db=db_session)
    assert fetched.notice_id == notice_id
    assert fetched.title == "Library Working Hours Update"

    # 404 Not Found
    with pytest.raises(HTTPException) as exc_info:
        get_notice(notice_id="FS-GMU-2099-NONEXISTENT", db=db_session)
    assert exc_info.value.status_code == 404


def test_list_notices_and_filters(db_session, test_admin, test_storage, sample_pdf_content, monkeypatch):
    """Test notice listing with category filtering, status filtering, and keyword search."""
    from app.services import notice_service
    monkeypatch.setattr(notice_service, "get_storage_service", lambda: test_storage)

    # Notice 1: Academic
    up1 = create_mock_upload_file(sample_pdf_content, "acad.pdf", "application/pdf")
    create_new_notice(
        title="Academic Calendar 2026-27",
        description="Important term dates",
        category="Academic",
        publication_status="published",
        file=up1,
        current_admin=test_admin,
        db=db_session,
    )

    # Notice 2: Admissions
    up2 = create_mock_upload_file(sample_pdf_content, "admit.pdf", "application/pdf")
    create_new_notice(
        title="PhD Admissions Shortlist",
        description="Interview candidates list",
        category="Admissions",
        publication_status="published",
        file=up2,
        current_admin=test_admin,
        db=db_session,
    )

    # List all
    all_notices = get_notices(page=1, page_size=20, db=db_session)
    assert all_notices.total >= 2

    # Filter by category
    acad_notices = get_notices(page=1, page_size=20, category="Academic", db=db_session)
    assert all("Academic" in item.category for item in acad_notices.items)

    # Search keyword
    searched = get_notices(page=1, page_size=20, search="Shortlist", db=db_session)
    assert any("PhD Admissions Shortlist" in item.title for item in searched.items)


def test_patch_notice_status(db_session, test_admin, test_storage, sample_pdf_content, monkeypatch):
    """Test updating notice publication status from draft to published to archived."""
    from app.services import notice_service
    monkeypatch.setattr(notice_service, "get_storage_service", lambda: test_storage)

    upload = create_mock_upload_file(sample_pdf_content, "draft.pdf", "application/pdf")
    created = create_new_notice(
        title="Tentative Draft Circular",
        description="Under review",
        category="General",
        publication_status="draft",
        file=upload,
        current_admin=test_admin,
        db=db_session,
    )
    notice_id = created.notice_id
    assert created.publication_status == "draft"

    # Patch to published
    pub_res = patch_notice_status(
        notice_id=notice_id,
        status_update=NoticeStatusUpdate(publication_status="published"),
        current_admin=test_admin,
        db=db_session,
    )
    assert pub_res.publication_status == "published"

    # Patch to archived
    arch_res = patch_notice_status(
        notice_id=notice_id,
        status_update=NoticeStatusUpdate(publication_status="archived"),
        current_admin=test_admin,
        db=db_session,
    )
    assert arch_res.publication_status == "archived"


def test_download_notice_file_stream(db_session, test_admin, test_storage, sample_pdf_content, monkeypatch):
    """Test streaming original notice document file."""
    from app.services import notice_service
    from app.routers import notices as notices_router_mod
    monkeypatch.setattr(notice_service, "get_storage_service", lambda: test_storage)
    monkeypatch.setattr(notices_router_mod, "get_storage_service", lambda: test_storage)

    upload = create_mock_upload_file(sample_pdf_content, "timetable.pdf", "application/pdf")
    created = create_new_notice(
        title="Semester Timetable",
        description=None,
        category="Academic",
        publication_status="published",
        file=upload,
        current_admin=test_admin,
        db=db_session,
    )
    notice_id = created.notice_id

    file_resp = download_notice_file(notice_id=notice_id, db=db_session)
    assert file_resp.body == sample_pdf_content
    assert file_resp.media_type == "application/pdf"
    assert "timetable.pdf" in file_resp.headers["Content-Disposition"]
