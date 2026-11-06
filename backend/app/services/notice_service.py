"""
Notice Service
Orchestrates official notice creation, storage persistence, unique Notice ID generation,
cryptographic SHA-256 hashing, Ed25519 digital signing, QR code generation,
robust watermarking, and secure distribution publishing.
"""

import datetime
import json
import logging
import math
import os
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.models.admin import Admin
from app.models.notice import Notice
from app.services.hash_service import HashService
from app.services.pdf_publishing_service import get_pdf_publishing_service
from app.services.qr_service import get_qr_service
from app.services.signature_service import (
    SignatureService,
    get_signature_service,
    METADATA_VERSION,
    SIGNATURE_ALGORITHM,
    HASH_ALGORITHM,
)
from app.services.storage_service import StorageService, get_storage_service
from app.services.watermark_service import get_watermark_service
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
    signature_service: Optional[SignatureService] = None,
) -> Notice:
    """
    Create, persist, cryptographically hash, and digitally sign a new official college notice.
    Workflow:
    1. Validates and saves original file into storage.
    2. Calculates SHA-256 hash using chunked hashing.
    3. Builds deterministic canonical metadata protecting notice ID, title, issuer, timestamp, and hash.
    4. Digitally signs the canonical metadata using the active Ed25519 private key.
    5. Persists notice entity in database with distribution_status = 'SIGNED'.
    """
    storage = storage or get_storage_service()
    signature_service = signature_service or get_signature_service()

    # 1. Normalize status
    norm_status = (publication_status or "published").strip().lower()
    if norm_status not in ("draft", "published", "archived"):
        norm_status = "published"

    # 2. Generate institutional unique Notice ID (e.g. FS-GMU-2026-A8F29C)
    unique_notice_id = generate_unique_notice_id(db)

    # 3. Store uploaded original file safely via StorageService
    stored_path = storage.save_file(
        content=file_bytes,
        original_filename=filename,
        subfolder="notices",
    )

    # 4. Phase 3: Cryptographic SHA-256 Hashing
    hash_result = HashService.calculate_bytes_hash(file_bytes)
    sha256_digest = hash_result["hash"]

    # 5. Phase 3: Build Canonical Signed Metadata
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    now_iso = now_utc.isoformat()
    active_key_id = signature_service._active_key_id or "default-key"

    canonical_metadata = signature_service.create_canonical_metadata(
        notice_id=unique_notice_id,
        title=title.strip(),
        description=description.strip() if description else "",
        category=category.strip() if category else "General",
        issuer_name=admin.full_name,
        issuer_id=str(admin.id),
        created_at_iso=now_iso,
        sha256_hash=sha256_digest,
        signing_key_id=active_key_id,
        metadata_version=METADATA_VERSION,
    )

    # 6. Phase 3: Digital Signing using Ed25519 Private Key
    signature_hex, used_key_id = signature_service.sign_metadata(
        metadata=canonical_metadata,
        key_id=active_key_id,
    )

    # 7. Construct Notice entity
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
        created_at=now_utc,
        updated_at=now_utc,
        # Phase 3 Fields
        sha256_hash=sha256_digest,
        hash_algorithm=HASH_ALGORITHM,
        digital_signature=signature_hex,
        signature_algorithm=SIGNATURE_ALGORITHM,
        signing_key_id=used_key_id,
        signed_metadata=json.dumps(canonical_metadata, sort_keys=True),
        metadata_version=METADATA_VERSION,
        signed_at=now_utc,
        distribution_status="SIGNED",
    )

    db.add(notice)
    db.commit()
    db.refresh(notice)

    logger.info(
        "Notice created & signed successfully: ID='%s' (SHA-256=%s, Key=%s)",
        notice.notice_id,
        notice.sha256_hash[:16],
        notice.signing_key_id,
    )
    return notice


def publish_notice(
    db: Session,
    notice_id: str,
    admin: Admin,
) -> Notice:
    """
    Phase 4: Officially publish a cryptographically signed notice.
    Workflow:
    1. Validates that the digital signature is valid before publishing.
    2. Generates unique official QR code with verification URL.
    3. Produces a distribution copy:
       - For PDFs: overlays the verification QR code stamp.
       - For Images: embeds a 2D-DCT digital watermark with notice reference.
    4. Updates publication_timestamp and sets distribution_status = 'PUBLISHED'.
    """
    notice = get_notice_by_notice_id(db, notice_id)
    if not notice:
        raise ValueError(f"Notice not found: {notice_id}")

    if not notice.digital_signature or not notice.signed_metadata:
        raise ValueError("Cannot publish notice: missing cryptographic signature.")

    # Verify signature before publishing
    signature_service = get_signature_service()
    metadata_dict = json.loads(notice.signed_metadata)
    verdict, reason = signature_service.verify_signature(
        metadata=metadata_dict,
        signature_hex=notice.digital_signature,
        key_id=notice.signing_key_id,
    )
    if verdict != "VALID_SIGNATURE":
        raise ValueError(f"Cannot publish notice: signature verification failed ({verdict}: {reason})")

    storage = get_storage_service()
    qr_service = get_qr_service()
    watermark_service = get_watermark_service()
    pdf_service = get_pdf_publishing_service()

    # 1. Generate QR Code
    qr_path, verification_url = qr_service.generate_qr_code(notice.notice_id)
    notice.qr_code_path = qr_path
    notice.verification_url = verification_url

    # 2. Generate Distribution Copy
    original_abs_path = storage.get_absolute_path(notice.stored_file_path)

    if notice.mime_type == "application/pdf":
        published_path = pdf_service.generate_published_pdf(
            original_pdf_path=original_abs_path,
            notice_id=notice.notice_id,
            verification_url=verification_url,
        )
        notice.published_file_path = published_path
        notice.watermark_version = "1.0-QR-STAMP"
        notice.watermark_reference = notice.notice_id
    elif notice.mime_type in ("image/png", "image/jpeg", "image/jpg"):
        watermarked_path, wm_ref = watermark_service.embed_watermark(
            input_image_path=original_abs_path,
            notice_id=notice.notice_id,
        )
        notice.watermarked_file_path = watermarked_path
        notice.published_file_path = watermarked_path
        notice.watermark_version = "1.0-DCT"
        notice.watermark_reference = wm_ref
    else:
        # Fallback distribution
        notice.published_file_path = original_abs_path

    # 3. Update Status
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    notice.publication_status = "published"
    notice.distribution_status = "PUBLISHED"
    notice.publication_timestamp = now_utc
    notice.updated_at = now_utc

    db.commit()
    db.refresh(notice)

    logger.info(
        "Notice '%s' published successfully (QR=%s, Distribution=%s)",
        notice.notice_id,
        notice.qr_code_path,
        notice.published_file_path,
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
        query = query.filter(
            or_(
                Notice.publication_status == status.strip().lower(),
                Notice.distribution_status == status.strip().upper(),
            )
        )

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


def revoke_notice(db: Session, notice_id: str, admin: Admin, reason: str) -> Notice:
    """Revoke an issued notice if compromised or recalled."""
    notice = get_notice_by_notice_id(db, notice_id)
    if not notice:
        raise ValueError(f"Notice not found: {notice_id}")

    now_utc = datetime.datetime.now(datetime.timezone.utc)
    notice.revoked_at = now_utc
    notice.distribution_status = "REVOKED"
    notice.publication_status = "archived"
    notice.updated_at = now_utc

    db.commit()
    db.refresh(notice)
    logger.warning("Notice '%s' revoked by %s. Reason: %s", notice_id, admin.email, reason)
    return notice
