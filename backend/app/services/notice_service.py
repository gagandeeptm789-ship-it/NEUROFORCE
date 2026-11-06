"""
Notice Service
Orchestrates official notice creation, storage persistence, unique Notice ID generation,
retrieval, filtering, status transitions, and prepares Phase 3 signing hooks.
"""

import datetime
import logging
import math
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.models.admin import Admin
from app.models.notice import Notice
from app.services.crypto_service import ICryptoService, get_crypto_service
from app.services.storage_service import StorageService, get_storage_service
from app.utils.notice_id import generate_unique_notice_id

logger = logging.getLogger("forwarded_seal.notices")


def create_notice(
    db: Session,
    admin: Admin,
    title: str,
    description: Optional[str],
    category: str,
    publication_status: str,
    file_bytes: bytes,
    filename: str,
    mime_type: str,
    file_size: int,
    storage: Optional[StorageService] = None,
) -> Notice:
    """
    Create and persist a new official college notice.
    - Generates a collision-resistant institutional Notice ID (e.g. FS-GMU-2026-A8F29C).
    - Persists original document file via the abstracted StorageService.
    - Saves metadata in PostgreSQL/SQLite.
    """
    storage = storage or get_storage_service()

    # 1. Normalize status
    norm_status = (publication_status or "published").strip().lower()
    if norm_status not in ("draft", "published", "archived"):
        norm_status = "published"

    # 2. Generate institutional unique Notice ID
    unique_notice_id = generate_unique_notice_id(db)

    # 3. Store uploaded file safely via StorageService
    stored_path = storage.save_file(
        content=file_bytes,
        original_filename=filename,
        subfolder="notices",
    )

    # 4. Construct Notice entity
    notice = Notice(
        notice_id=unique_notice_id,
        title=title.strip(),
        description=description.strip() if description else None,
        category=category.strip() if category else "General",
        original_filename=filename,
        stored_file_path=stored_path,
        mime_type=mime_type,
        file_size=file_size,
        issuer_admin_id=admin.id,
        publication_status=norm_status,
    )

    db.add(notice)
    db.commit()
    db.refresh(notice)

    logger.info(
        "Notice created successfully: ID='%s' by Admin '%s' (title='%s')",
        notice.notice_id,
        admin.email,
        notice.title,
    )
    return notice


def get_notice_by_notice_id(db: Session, notice_id: str) -> Optional[Notice]:
    """Retrieve notice metadata by unique Notice ID (e.g. FS-GMU-2026-A8F29C)."""
    if not notice_id:
        return None
    return (
        db.query(Notice)
        .options(joinedload(Notice.issuer_admin))
        .filter(Notice.notice_id == notice_id.strip())
        .first()
    )


def get_notice_by_id(db: Session, id_val: str) -> Optional[Notice]:
    """Retrieve notice by internal UUID or notice_id."""
    if not id_val:
        return None
    return (
        db.query(Notice)
        .options(joinedload(Notice.issuer_admin))
        .filter(or_(Notice.id == id_val.strip(), Notice.notice_id == id_val.strip()))
        .first()
    )


def list_notices(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    category: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
) -> Tuple[List[Notice], int, int]:
    """
    Query notices with pagination, category filter, publication status, and text search.
    Returns: (notices_list, total_count, total_pages)
    """
    page = max(1, page)
    page_size = min(max(1, page_size), 100)

    query = db.query(Notice).options(joinedload(Notice.issuer_admin))

    # Optional status filter
    if status and status.lower() != "all":
        query = query.filter(Notice.publication_status == status.strip().lower())

    # Optional category filter
    if category and category.lower() != "all":
        query = query.filter(Notice.category.ilike(f"%{category.strip()}%"))

    # Optional search in title or description
    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Notice.title.ilike(search_term),
                Notice.description.ilike(search_term),
                Notice.notice_id.ilike(search_term),
            )
        )

    total_count = query.count()
    total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1

    items = (
        query.order_by(Notice.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return items, total_count, total_pages


def update_notice_status(db: Session, notice: Notice, new_status: str) -> Notice:
    """Update publication status of a notice (draft, published, archived)."""
    clean_status = new_status.strip().lower()
    if clean_status not in ("draft", "published", "archived"):
        raise ValueError("Invalid status. Allowed values: draft, published, archived")

    notice.publication_status = clean_status
    notice.updated_at = datetime.datetime.now(datetime.timezone.utc)
    db.commit()
    db.refresh(notice)
    logger.info("Notice '%s' status updated to '%s'", notice.notice_id, clean_status)
    return notice


# ==============================================================================
# Phase 3 Extensibility Hooks
# ==============================================================================

def prepare_phase3_signing_payload(
    notice: Notice,
    storage: Optional[StorageService] = None,
    crypto: Optional[ICryptoService] = None,
) -> Dict[str, Any]:
    """
    Read the original stored file, calculate SHA-256 hash, and format
    canonical metadata for Phase 3 asymmetric digital signing.
    """
    storage = storage or get_storage_service()
    crypto = crypto or get_crypto_service()

    file_bytes = storage.get_file(notice.stored_file_path)
    file_sha256 = crypto.calculate_sha256(file_bytes)

    signed_metadata = crypto.generate_signed_metadata(
        notice_id=notice.notice_id,
        file_sha256=file_sha256,
        issuer_id=notice.issuer_admin_id,
        timestamp_iso=notice.created_at.isoformat(),
    )

    return {
        "notice_id": notice.notice_id,
        "sha256_hash": file_sha256,
        "metadata_payload": signed_metadata,
    }

