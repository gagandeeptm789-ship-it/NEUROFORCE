"""
End-to-End Verification API Tests (Phase 5 & 7)
Verifies student verification pipeline, 4 primary result categories,
revocation handling, watermark extraction, and public key discovery.
"""

import io
import json
import os
import shutil
import tempfile
import cv2
import numpy as np
from PIL import Image, ImageDraw
import pytest
from fastapi import UploadFile

from app.models.notice import Notice
from app.routers.verification import (
    extract_watermark_endpoint,
    get_active_public_key,
    get_public_key_by_id,
    verify_file_integrity,
    verify_notice,
    verify_notice_by_id,
    verify_notice_signature,
)
from app.schemas.notice import SignatureVerificationRequest
from app.services.crypto_service import get_crypto_service
from app.services.hash_service import HashService
from app.services.qr_service import get_qr_service
from app.services.signature_service import get_signature_service
from app.services.watermark_service import get_watermark_service


def _build_test_notice_image(title: str, text: str) -> bytes:
    """Generate PNG bytes of a notice with header, body and footer."""
    img = Image.new("RGB", (800, 1000), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.rectangle([30, 30, 770, 110], fill=(240, 245, 255), outline=(15, 23, 42), width=2)
    draw.text((50, 50), "GLOBAL METROPOLITAN UNIVERSITY", fill=(15, 23, 42))
    draw.text((50, 80), "OFFICIAL CIRCULAR", fill=(71, 85, 105))
    draw.text((50, 160), title, fill=(15, 23, 42))
    draw.text((50, 220), text, fill=(30, 41, 59))
    draw.rectangle([30, 910, 770, 970], fill=(248, 250, 252), outline=(15, 23, 42), width=1)
    draw.text((50, 935), "AUTHORIZED SIGNATORY: Academic Registrar", fill=(15, 23, 42))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def registered_published_notice(db_session, test_admin, temp_storage_dir):
    """Seed a fully signed and published notice in the database with actual stored file."""
    notice_id = "FS-GMU-2026-VTEST01"
    title = "Semester Examination Guidelines 2026"
    category = "Examinations"
    description = "Official guidelines for spring end-semester examinations."

    img_bytes = _build_test_notice_image(title, "Mandatory exam attendance: 75% required.")
    calc_hash = HashService.calculate_bytes_hash(img_bytes)["hash"]

    # Save to disk
    stored_path = os.path.join(temp_storage_dir, f"{notice_id}_original.png")
    with open(stored_path, "wb") as f:
        f.write(img_bytes)

    # Sign notice with active key
    sig_service = get_signature_service()
    key_info = sig_service.get_active_public_key_info()
    key_id = key_info["key_id"]

    canonical_meta = {
        "notice_id": notice_id,
        "title": title,
        "category": category,
        "document_sha256": calc_hash,
        "version": "1.0",
        "created_at_iso": "2026-04-01T10:00:00Z",
    }
    signature, _ = sig_service.sign_metadata(canonical_meta, key_id)

    notice = Notice(
        notice_id=notice_id,
        title=title,
        description=description,
        category=category,
        original_filename="guidelines.png",
        stored_file_path=stored_path,
        mime_type="image/png",
        file_size=len(img_bytes),
        issuer_admin_id=test_admin.id,
        publication_status="published",
        sha256_hash=calc_hash,
        digital_signature=signature,
        signing_key_id=key_id,
        signed_metadata=json.dumps(canonical_meta),
    )
    db_session.add(notice)
    db_session.commit()
    db_session.refresh(notice)

    return {
        "notice": notice,
        "img_bytes": img_bytes,
        "stored_path": stored_path,
        "hash": calc_hash,
    }


def test_verify_by_notice_id_lookup(db_session, registered_published_notice):
    """Category A: Student verifies by Notice ID alone -> returns VERIFIED."""
    notice = registered_published_notice["notice"]
    res = verify_notice_by_id(notice_id=notice.notice_id, db=db_session)

    assert res.status == "VERIFIED"
    assert res.matchScore == 100
    assert res.notice_id == notice.notice_id
    assert res.signature_valid is True
    assert res.securityAudit.cryptographicSignature == "VALID_MATCH"


def test_verify_exact_byte_match(db_session, registered_published_notice):
    """Category A: Student uploads original byte-for-byte identical file -> returns VERIFIED."""
    notice = registered_published_notice["notice"]
    img_bytes = registered_published_notice["img_bytes"]

    upload = UploadFile(
        file=io.BytesIO(img_bytes),
        filename="official_guidelines.png",
        headers={"content-type": "image/png"},
    )

    res = verify_notice(file=upload, notice_id=notice.notice_id, db=db_session)

    assert res.status == "VERIFIED"
    assert res.matchScore == 100
    assert res.sha256_match is True
    assert res.signature_valid is True
    assert res.securityAudit.pixelForensics == "CLEAN_NO_ALTERATION"


def test_verify_authentic_but_transformed(db_session, registered_published_notice):
    """Category B: Student uploads authentic notice forwarded via WhatsApp/compressed as JPEG."""
    notice = registered_published_notice["notice"]
    img_bytes = registered_published_notice["img_bytes"]

    # Re-encode as JPEG (lossy compression)
    pil_img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    buf = io.BytesIO()
    pil_img.save(buf, format="JPEG", quality=80)
    compressed_bytes = buf.getvalue()

    upload = UploadFile(
        file=io.BytesIO(compressed_bytes),
        filename="forwarded_notice.jpg",
        headers={"content-type": "image/jpeg"},
    )

    res = verify_notice(file=upload, notice_id=notice.notice_id, db=db_session)

    assert res.status == "AUTHENTIC_TRANSFORMED"
    assert res.matchScore >= 85
    assert res.sha256_match is False  # Bytes differ
    assert res.signature_valid is True
    assert res.securityAudit.pixelForensics == "JPEG_COMPRESSION_ARTIFACTS_ONLY"
    assert len(res.forensicReport.suspicious_regions) == 0


def test_verify_tampering_detected(db_session, registered_published_notice):
    """Category C: Student uploads altered copy (postponed date spliced over original)."""
    notice = registered_published_notice["notice"]
    img_bytes = registered_published_notice["img_bytes"]

    # Splice altered text
    pil_img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    draw = ImageDraw.Draw(pil_img)
    draw.rectangle([50, 220, 600, 250], fill=(255, 255, 255))
    draw.text((50, 220), "ALL EXAMS CANCELLED AND GRADES PROMOTED.", fill=(220, 0, 0))

    buf = io.BytesIO()
    pil_img.save(buf, format="PNG")
    tampered_bytes = buf.getvalue()

    upload = UploadFile(
        file=io.BytesIO(tampered_bytes),
        filename="altered_notice.png",
        headers={"content-type": "image/png"},
    )

    res = verify_notice(file=upload, notice_id=notice.notice_id, db=db_session)

    assert res.status == "TAMPERING_DETECTED"
    assert res.matchScore < 80
    assert len(res.forensicReport.suspicious_regions) >= 1
    assert res.forensicReport.annotated_preview is not None
    assert res.forensicReport.difference_preview is not None


def test_verify_copied_qr_attack(db_session, registered_published_notice):
    """Category C: Attacker pastes authentic Notice ID / QR onto completely fake document."""
    notice = registered_published_notice["notice"]

    # Create completely fake document
    fake_img = Image.new("RGB", (800, 1000), color=(255, 255, 255))
    draw = ImageDraw.Draw(fake_img)
    draw.text((50, 50), "UNOFFICIAL REFUND POLICY", fill=(0, 0, 0))
    buf = io.BytesIO()
    fake_img.save(buf, format="PNG")
    fake_bytes = buf.getvalue()

    upload = UploadFile(
        file=io.BytesIO(fake_bytes),
        filename="fake_with_copied_id.png",
        headers={"content-type": "image/png"},
    )

    # Pass authentic Notice ID as if copied QR had decoded it
    res = verify_notice(file=upload, notice_id=notice.notice_id, qr_data=notice.notice_id, db=db_session)

    assert res.status == "TAMPERING_DETECTED"
    assert any("Copied QR Code Attack" in a for a in res.securityAudit.detectedAnomalies)


def test_verify_unverifiable_unknown_notice(db_session):
    """Category D: Notice ID not in registry -> UNVERIFIABLE."""
    res = verify_notice_by_id(notice_id="FS-UNKNOWN-9999-XXXXXX", db=db_session)

    assert res.status == "UNVERIFIABLE"
    assert res.matchScore == 0
    assert "not found" in res.securityAudit.verdictSummary.lower()


def test_verify_revoked_notice(db_session, registered_published_notice):
    """Special Condition: Notice has been officially revoked."""
    from datetime import datetime, timezone
    notice = registered_published_notice["notice"]
    notice.revoked_at = datetime.now(timezone.utc)
    db_session.commit()

    res = verify_notice_by_id(notice_id=notice.notice_id, db=db_session)

    assert res.status == "TAMPERING_DETECTED"
    assert "REVOKED" in res.securityAudit.verdictSummary
    assert res.signature_valid is False


def test_public_key_retrieval():
    """Verify active and ID-based Ed25519 public key retrieval."""
    active_key = get_active_public_key()
    assert active_key.status == "active"
    assert "PUBLIC KEY" in active_key.public_key_pem

    key_by_id = get_public_key_by_id(active_key.key_id)
    assert key_by_id.key_id == active_key.key_id
    assert key_by_id.public_key_pem == active_key.public_key_pem


def test_file_byte_integrity_endpoint(db_session, registered_published_notice):
    """Verify byte-for-byte integrity endpoint."""
    notice = registered_published_notice["notice"]
    img_bytes = registered_published_notice["img_bytes"]

    upload = UploadFile(
        file=io.BytesIO(img_bytes),
        filename="test.png",
        headers={"content-type": "image/png"},
    )

    res = verify_file_integrity(notice_id=notice.notice_id, file=upload, db=db_session)
    assert res.status == "EXACT_MATCH"
    assert res.is_exact_match is True
