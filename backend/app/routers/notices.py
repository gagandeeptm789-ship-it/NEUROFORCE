"""
Notice Router
Endpoints for creating official college notices, uploading document attachments,
querying notices with pagination/filters, retrieving individual notices, and updating status.
"""

import logging
from typing import Optional
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import decode_access_token, security_bearer
from app.database import get_db
from app.models.admin import Admin
from app.models.notice import Notice
from app.schemas.notice import (
    AdminBrief,
    NoticeDashboardStats,
    NoticeListResponse,
    NoticeResponse,
    NoticeStatusUpdate,
    PublishNoticeResponse,
    WatermarkInfoResponse,
)
from app.services.auth_service import get_admin_by_id, get_current_active_admin
from app.services.notice_service import (
    create_notice,
    get_notice_by_id,
    get_notice_by_notice_id,
    list_notices,
    publish_notice,
    revoke_notice,
    update_notice_status,
)
from app.services.storage_service import get_storage_service
from app.utils.file_validator import validate_uploaded_file

logger = logging.getLogger("forwarded_seal.notices_router")
settings = get_settings()

router = APIRouter(prefix="/notices", tags=["College Notices"])


def format_notice_response(notice) -> NoticeResponse:
    """Format SQLAlchemy Notice model into Pydantic NoticeResponse schema."""
    issuer_brief = None
    if notice.issuer_admin:
        issuer_brief = AdminBrief.model_validate(notice.issuer_admin)

    download_url = f"{settings.API_V1_PREFIX}/notices/{notice.notice_id}/file"

    return NoticeResponse(
        id=str(notice.id),
        notice_id=notice.notice_id,
        title=notice.title,
        description=notice.description,
        category=notice.category,
        original_filename=notice.original_filename,
        mime_type=notice.mime_type,
        file_size=notice.file_size,
        publication_status=notice.publication_status,
        issuer_admin_id=str(notice.issuer_admin_id),
        created_at=notice.created_at,
        updated_at=notice.updated_at,
        issuer_admin=issuer_brief,
        file_download_url=download_url,
        sha256_hash=notice.sha256_hash,
        digital_signature=notice.digital_signature,
        signing_key_id=notice.signing_key_id,
        signed_metadata=notice.signed_metadata,
        revoked_at=notice.revoked_at,
    )


def get_optional_current_admin(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: Session = Depends(get_db),
) -> Optional[Admin]:
    """Extract authenticated admin if Bearer token is provided, or return None."""
    if not credentials or credentials.scheme.lower() != "bearer":
        return None
    try:
        payload = decode_access_token(credentials.credentials)
        admin_id = payload.get("sub")
        if admin_id:
            admin = get_admin_by_id(db, admin_id)
            if admin and admin.is_active:
                return admin
    except Exception:
        pass
    return None


@router.post(
    "",
    response_model=NoticeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Official Notice",
    description=(
        "Upload a document (PDF, PNG, JPG) and publish an official college notice. "
        "Requires administrator Bearer authentication. Generates a unique Notice ID."
    ),
)
def create_new_notice(
    title: str = Form(..., min_length=3, max_length=255, description="Headline of the notice"),
    description: Optional[str] = Form(None, description="Detailed text or summary"),
    category: str = Form("General", description="Category: Academic, Examination, Admissions, etc."),
    publication_status: str = Form("published", description="Status: draft or published"),
    file: UploadFile = File(..., description="Official document (PDF or Image)"),
    current_admin: Admin = Depends(get_current_active_admin),
    db: Session = Depends(get_db),
):
    """Create an official notice with file attachment."""
    # 1. Validate file content type, size, and magic bytes
    file_bytes, clean_filename, detected_mime, file_size = validate_uploaded_file(file)

    # 2. Persist notice and document
    notice = create_notice(
        db=db,
        admin=current_admin,
        title=title,
        description=description,
        category=category,
        publication_status=publication_status,
        file_bytes=file_bytes,
        filename=clean_filename,
        mime_type=detected_mime,
        file_size=file_size,
    )

    return format_notice_response(notice)


@router.get(
    "",
    response_model=NoticeListResponse,
    summary="List Notices",
    description="Retrieve paginated notices with optional category, status, and search filters.",
)
def get_notices(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    category: Optional[str] = Query(None, description="Filter by category"),
    status: Optional[str] = Query(None, description="Filter: published, draft, archived, all"),
    search: Optional[str] = Query(None, description="Search keyword in title or description"),
    current_admin: Optional[Admin] = Depends(get_optional_current_admin),
    db: Session = Depends(get_db),
):
    """Query notices list."""
    # Handle direct Python function invocation where default is Query object
    from fastapi.params import Query as QueryParam
    filter_category = None if isinstance(category, QueryParam) else category
    filter_status = None if isinstance(status, QueryParam) else status
    filter_search = None if isinstance(search, QueryParam) else search

    # Public callers must never be able to request draft or archived notices.
    if not current_admin:
        filter_status = "published"

    items, total, total_pages = list_notices(
        db=db,
        page=page,
        page_size=page_size,
        category=filter_category,
        status=filter_status,
        search=filter_search,
    )

    formatted_items = [format_notice_response(n) for n in items]
    stats_query = db.query(Notice)
    if not current_admin:
        stats_query = stats_query.filter(Notice.publication_status == "published")
    total_notices = stats_query.with_entities(func.count(Notice.id)).scalar() or 0
    published_notices = (
        total_notices
        if not current_admin
        else db.query(func.count(Notice.id))
        .filter(Notice.publication_status == "published")
        .scalar()
        or 0
    )
    return NoticeListResponse(
        items=formatted_items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        stats=NoticeDashboardStats(
            total_notices=total_notices,
            published_notices=published_notices,
        ),
    )


@router.get(
    "/{notice_id}",
    response_model=NoticeResponse,
    summary="Get Notice by ID",
    description="Retrieve notice metadata by its unique Notice ID (e.g. FS-GMU-2026-A8F29C) or internal UUID.",
)
def get_notice(
    notice_id: str,
    db: Session = Depends(get_db),
):
    """Retrieve an individual notice by Notice ID."""
    notice = get_notice_by_id(db, notice_id)
    if not notice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notice '{notice_id}' was not found.",
        )
    return format_notice_response(notice)


@router.patch(
    "/{notice_id}/status",
    response_model=NoticeResponse,
    summary="Update Notice Status",
    description="Update the publication status of a notice (draft, published, or archived). Requires admin auth.",
)
def patch_notice_status(
    notice_id: str,
    status_update: NoticeStatusUpdate,
    current_admin: Admin = Depends(get_current_active_admin),
    db: Session = Depends(get_db),
):
    """Update publication status of a notice."""
    notice = get_notice_by_id(db, notice_id)
    if not notice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notice '{notice_id}' was not found.",
        )

    try:
        updated = update_notice_status(db, notice, status_update.publication_status)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return format_notice_response(updated)


@router.get(
    "/{notice_id}/file",
    summary="Download Notice Document",
    description="Stream the original uploaded notice file (PDF or Image) safely.",
)
def download_notice_file(
    notice_id: str,
    db: Session = Depends(get_db),
):
    """Stream notice document file with appropriate MIME headers."""
    notice = get_notice_by_id(db, notice_id)
    if not notice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notice '{notice_id}' was not found.",
        )

    storage = get_storage_service()
    try:
        file_bytes = storage.get_file(notice.stored_file_path)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stored document file was not found on server.",
        )

    # Safe Content-Disposition header
    safe_filename = notice.original_filename.replace('"', '\\"')
    headers = {
        "Content-Disposition": f'inline; filename="{safe_filename}"',
        "Content-Length": str(len(file_bytes)),
        "X-Content-Type-Options": "nosniff",
    }

    return Response(
        content=file_bytes,
        media_type=notice.mime_type,
        headers=headers,
    )
