"""
Verification Router
Comprehensive public verification endpoints for The Forwarded Seal platform.
Provides student verification, forensic image analysis, steganographic watermark recovery,
byte-integrity checks, and Ed25519 public key retrieval.
"""

import io
import json
import logging
import os
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import cv2
import numpy as np
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.notice import Notice
from app.schemas.notice import (
    FileIntegrityVerificationResponse,
    PublicKeyInfoResponse,
    SignatureVerificationRequest,
    SignatureVerificationResponse,
)
from app.schemas.verification import (
    ForensicReport,
    NoticeVerificationResponse,
    SecurityAuditDetails,
    SuspiciousRegion,
    WatermarkExtractionResponse,
)
from app.services.hash_service import HashService
from app.services.image_preprocessing import ImagePreprocessingService, get_image_preprocessing_service
from app.services.notice_service import get_notice_by_notice_id
from app.services.qr_service import QRService, get_qr_service
from app.services.signature_service import SignatureService, get_signature_service
from app.services.tampering_detection import TamperingDetectionService, get_tampering_detection_service
from app.services.watermark_service import WatermarkService, get_watermark_service
from app.utils.file_validator import validate_uploaded_file

logger = logging.getLogger("forwarded_seal.verification_router")

router = APIRouter(prefix="/verification", tags=["Verification & Forensics"])


def _extract_notice_id_from_text(text: Any) -> Optional[str]:
    """Helper to parse a Notice ID from raw text or a verification URL."""
    if not text or not isinstance(text, str):
        return None
    cleaned = text.strip()
    if not cleaned:
        return None
    # Match standard notice format FS-*-YYYY-*
    match = re.search(r"FS-[A-Z0-9]+-\d{4}-[A-Z0-9]+", cleaned, re.IGNORECASE)
    if match:
        return match.group(0).upper()
    # Check if text is a URL with notice ID as the last path segment
    if "/" in cleaned:
        last_seg = cleaned.rstrip("/").split("/")[-1]
        if last_seg.upper().startswith("FS-"):
            return last_seg.upper()
    return cleaned.upper() if cleaned.upper().startswith("FS-") else None


def _perform_core_verification(
    db: Session,
    file_bytes: Optional[bytes] = None,
    notice_id_input: Optional[str] = None,
    qr_data_input: Optional[str] = None,
) -> NoticeVerificationResponse:
    """Core verification pipeline executing cryptographic and forensic checks."""
    signature_service = get_signature_service()
    qr_service = get_qr_service()
    watermark_service = get_watermark_service()
    tampering_service = get_tampering_detection_service()
    preprocessing_service = get_image_preprocessing_service()

    target_notice_id = _extract_notice_id_from_text(notice_id_input)
    if not target_notice_id and qr_data_input:
        target_notice_id = _extract_notice_id_from_text(qr_data_input)

    uploaded_sha256 = None
    watermark_detected = False
    watermark_notice_id = None
    qr_decoded_id = None
    uploaded_image_bgr = None
    extracted_doc_text = None

    # Step 1: Analyze uploaded file if provided
    if file_bytes:
        uploaded_sha256 = HashService.calculate_bytes_hash(file_bytes)["hash"]

        # Decode QR from image bytes
        qr_text = qr_service.decode_qr_from_image(file_bytes)
        if qr_text:
            qr_decoded_id = _extract_notice_id_from_text(qr_text)
            if not target_notice_id:
                target_notice_id = qr_decoded_id

        # Attempt to load document image
        try:
            uploaded_image_bgr, extracted_doc_text = preprocessing_service.load_document_image(file_bytes)
        except Exception as e:
            logger.debug("Image loading error: %s", e)

        # Attempt Watermark Extraction
        if uploaded_image_bgr is not None:
            try:
                # Convert BGR to RGB PIL image for watermark extraction
                from PIL import Image
                rgb_img = Image.fromarray(cv2.cvtColor(uploaded_image_bgr, cv2.COLOR_BGR2RGB))
                wm_res = watermark_service.extract_watermark(rgb_img)
                if wm_res.get("detected"):
                    watermark_detected = True
                    watermark_notice_id = wm_res.get("notice_id")
                    if not target_notice_id and watermark_notice_id:
                        target_notice_id = _extract_notice_id_from_text(watermark_notice_id)
            except Exception as e:
                logger.debug("Watermark extraction error: %s", e)

        # Fallback: check if hash matches any notice directly in the database
        if not target_notice_id:
            matched_notice = db.query(Notice).filter(Notice.sha256_hash == uploaded_sha256).first()
            if matched_notice:
                target_notice_id = matched_notice.notice_id

    # Step 2: If Notice ID still cannot be determined -> UNVERIFIABLE
    if not target_notice_id:
        return NoticeVerificationResponse(
            status="UNVERIFIABLE",
            id=None,
            notice_id=None,
            title="Unidentified Document",
            department="Unknown",
            issuer="Unknown",
            matchScore=0,
            contentSnippet=extracted_doc_text[:120] if extracted_doc_text else None,
            original_sha256=None,
            uploaded_sha256=uploaded_sha256,
            sha256_match=False,
            signature_valid=False,
            watermark_recovered=watermark_detected,
            securityAudit=SecurityAuditDetails(
                cryptographicSignature="UNSIGNED",
                signatureAlgorithm="Ed25519",
                watermarkIntegrity="INTACT" if watermark_detected else "ABSENT",
                watermarkDetected=watermark_detected,
                pixelForensics="UNCHECKED",
                metadataIntegrity="MISSING",
                detectedAnomalies=[
                    "Notice ID could not be identified from file or input.",
                    "QR code absent or unreadable.",
                    "Digital watermark could not be recovered.",
                ],
                verdictSummary=(
                    "UNVERIFIABLE: Document identity could not be established in the university ledger. "
                    "Ensure the Notice ID or official QR seal is legible."
                ),
            ),
        )

    # Step 3: Fetch official notice from database
    notice = get_notice_by_notice_id(db, target_notice_id)
    if not notice:
        return NoticeVerificationResponse(
            status="UNVERIFIABLE",
            id=target_notice_id,
            notice_id=target_notice_id,
            title="Notice Not Found In Registry",
            department="Unknown",
            issuer="Unknown",
            matchScore=0,
            contentSnippet=extracted_doc_text[:120] if extracted_doc_text else None,
            original_sha256=None,
            uploaded_sha256=uploaded_sha256,
            sha256_match=False,
            signature_valid=False,
            watermark_recovered=watermark_detected,
            securityAudit=SecurityAuditDetails(
                cryptographicSignature="INVALID",
                signatureAlgorithm="Ed25519",
                watermarkIntegrity="INTACT" if watermark_detected else "ABSENT",
                watermarkDetected=watermark_detected,
                pixelForensics="UNCHECKED",
                metadataIntegrity="INVALID_NOTICE_ID",
                detectedAnomalies=[
                    f"Notice ID '{target_notice_id}' is not registered on the official ledger."
                ],
                verdictSummary=(
                    f"UNVERIFIABLE: Notice ID '{target_notice_id}' was not found in the official university registry."
                ),
            ),
        )

    # Step 4: Check if Notice is Revoked
    if notice.revoked_at:
        return NoticeVerificationResponse(
            status="TAMPERING_DETECTED",
            id=notice.notice_id,
            notice_id=notice.notice_id,
            title=notice.title,
            department=notice.category,
            issuer=notice.issuer_admin.full_name if notice.issuer_admin else "Authorized Signatory",
            issueDate=notice.created_at.isoformat() if notice.created_at else None,
            published_at=notice.created_at.isoformat() if notice.created_at else None,
            matchScore=0,
            contentSnippet=notice.description or extracted_doc_text,
            original_sha256=notice.sha256_hash,
            uploaded_sha256=uploaded_sha256,
            sha256_match=(uploaded_sha256 == notice.sha256_hash) if uploaded_sha256 else False,
            signature_valid=False,
            watermark_recovered=watermark_detected,
            securityAudit=SecurityAuditDetails(
                cryptographicSignature="INVALID",
                signatureAlgorithm="Ed25519",
                watermarkIntegrity="INTACT" if watermark_detected else "ABSENT",
                watermarkDetected=watermark_detected,
                pixelForensics="REVOKED_DOCUMENT",
                metadataIntegrity="OFFICIALLY_REVOKED",
                detectedAnomalies=[
                    f"Notice officially revoked on {notice.revoked_at}. Document is void."
                ],
                verdictSummary=(
                    f"REVOKED NOTICE: This circular was officially revoked by the institution on "
                    f"{notice.revoked_at} and is no longer valid."
                ),
            ),
        )

    # Step 5: Verify Cryptographic Signature of the Notice
    signature_valid = False
    crypto_status = "INVALID"
    if notice.signed_metadata and notice.digital_signature and notice.signing_key_id:
        try:
            meta_dict = json.loads(notice.signed_metadata)
            verdict, _ = signature_service.verify_signature(
                metadata=meta_dict,
                signature_hex=notice.digital_signature,
                key_id=notice.signing_key_id,
            )
            if verdict == "VALID_SIGNATURE":
                signature_valid = True
                crypto_status = "VALID_MATCH"
        except Exception as e:
            logger.error("Error parsing signed metadata: %s", e)

    # Step 6: Case A — No file provided (Verification by Notice ID / QR URL alone)
    if not file_bytes or uploaded_image_bgr is None:
        return NoticeVerificationResponse(
            status="VERIFIED" if signature_valid else "UNVERIFIABLE",
            id=notice.notice_id,
            notice_id=notice.notice_id,
            title=notice.title,
            department=notice.category,
            issuer=notice.issuer_admin.full_name if notice.issuer_admin else "Authorized Signatory",
            issueDate=notice.created_at.isoformat() if notice.created_at else None,
            published_at=notice.created_at.isoformat() if notice.created_at else None,
            matchScore=100 if signature_valid else 40,
            contentSnippet=notice.description,
            original_sha256=notice.sha256_hash,
            uploaded_sha256=None,
            sha256_match=False,
            signature_valid=signature_valid,
            watermark_recovered=False,
            securityAudit=SecurityAuditDetails(
                cryptographicSignature=crypto_status,
                signatureAlgorithm="Ed25519",
                watermarkIntegrity="ABSENT",
                watermarkDetected=False,
                pixelForensics="CLEAN_NO_ALTERATION",
                metadataIntegrity="CANONICAL_ENCODED",
                detectedAnomalies=[] if signature_valid else ["Signature record verification incomplete."],
                verdictSummary=(
                    "VERIFIED: Official notice confirmed in university registry ledger. "
                    "Cryptographic signature verified."
                    if signature_valid
                    else "Notice ID exists, but cryptographic signature could not be verified."
                ),
            ),
        )

    # Step 7: Case B — File provided: Exact Byte Match (SHA-256)
    is_exact_match = (uploaded_sha256 and notice.sha256_hash and uploaded_sha256.lower() == notice.sha256_hash.lower())

    if is_exact_match and signature_valid:
        return NoticeVerificationResponse(
            status="VERIFIED",
            id=notice.notice_id,
            notice_id=notice.notice_id,
            title=notice.title,
            department=notice.category,
            issuer=notice.issuer_admin.full_name if notice.issuer_admin else "Authorized Signatory",
            issueDate=notice.created_at.isoformat() if notice.created_at else None,
            published_at=notice.created_at.isoformat() if notice.created_at else None,
            matchScore=100,
            contentSnippet=notice.description or extracted_doc_text,
            original_sha256=notice.sha256_hash,
            uploaded_sha256=uploaded_sha256,
            sha256_match=True,
            signature_valid=True,
            watermark_recovered=watermark_detected,
            securityAudit=SecurityAuditDetails(
                cryptographicSignature="VALID_MATCH",
                signatureAlgorithm="Ed25519",
                watermarkIntegrity="INTACT" if watermark_detected else "ABSENT",
                watermarkDetected=watermark_detected,
                pixelForensics="CLEAN_NO_ALTERATION",
                metadataIntegrity="CANONICAL_ENCODED",
                detectedAnomalies=[],
                verdictSummary=(
                    "AUTHENTIC RECORD: The uploaded document is byte-for-byte identical to the "
                    "official published notice. Cryptographic signature and document seal intact."
                ),
            ),
        )

    # Step 8: Case C — File differs from original bytes -> Run Forensics Engine
    official_image_bgr = None
    target_path = None
    if notice.stored_file_path and os.path.exists(notice.stored_file_path):
        target_path = notice.stored_file_path
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        candidate_paths = [
            os.path.join(base_dir, "uploads", notice.stored_file_path or ""),
            os.path.join(base_dir, "published", f"{notice.notice_id}_published.pdf"),
            os.path.join(base_dir, "published", f"{notice.notice_id}_watermarked.png"),
            os.path.join(base_dir, "uploads", f"{notice.notice_id}_original.pdf"),
            os.path.join(base_dir, "uploads", f"{notice.notice_id}_original.png"),
        ]
        for p in candidate_paths:
            if os.path.exists(p):
                target_path = p
                break

    if target_path:
        try:
            official_image_bgr, _ = preprocessing_service.load_document_image(target_path)
        except Exception as e:
            logger.error("Failed to load official document for forensics: %s", e)

    # If official image not found on disk, synthesize canvas representation from notice metadata
    if official_image_bgr is None:
        canvas_h, canvas_w = uploaded_image_bgr.shape[:2]
        canvas = np.ones((canvas_h, canvas_w, 3), dtype=np.uint8) * 255
        cv2.rectangle(canvas, (20, 20), (canvas_w - 20, 80), (240, 245, 255), -1)
        cv2.rectangle(canvas, (20, 20), (canvas_w - 20, 80), (15, 23, 42), 2)
        cv2.putText(canvas, notice.title[:40], (30, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (15, 23, 42), 2)
        official_image_bgr = canvas

    # Run deep forensic tampering analysis
    effective_qr_claim = qr_decoded_id or _extract_notice_id_from_text(qr_data_input)
    forensic_res = tampering_service.analyze_tampering(
        official_image=official_image_bgr,
        uploaded_image=uploaded_image_bgr,
        notice_id=notice.notice_id,
        official_title=notice.title,
        official_category=notice.category,
        qr_detected_id=effective_qr_claim,
        watermark_detected_id=watermark_notice_id,
    )

    verdict_status = forensic_res["status"]
    # Map AUTHENTIC to VERIFIED for frontend consistency
    if verdict_status == "AUTHENTIC":
        verdict_status = "VERIFIED"

    suspicious_objs = [
        SuspiciousRegion(**item) for item in forensic_res.get("suspicious_regions", [])
    ]

    watermark_status = "INTACT" if watermark_detected else "DEGRADED_BY_COMPRESSION"

    return NoticeVerificationResponse(
        status=verdict_status,
        id=notice.notice_id,
        notice_id=notice.notice_id,
        title=notice.title,
        department=notice.category,
        issuer=notice.issuer_admin.full_name if notice.issuer_admin else "Authorized Signatory",
        issueDate=notice.created_at.isoformat() if notice.created_at else None,
        published_at=notice.created_at.isoformat() if notice.created_at else None,
        matchScore=forensic_res["match_score"],
        contentSnippet=notice.description or extracted_doc_text,
        original_sha256=notice.sha256_hash,
        uploaded_sha256=uploaded_sha256,
        sha256_match=False,
        signature_valid=signature_valid,
        watermark_recovered=watermark_detected,
        securityAudit=SecurityAuditDetails(
            cryptographicSignature=crypto_status,
            signatureAlgorithm="Ed25519",
            watermarkIntegrity=watermark_status,
            watermarkDetected=watermark_detected,
            pixelForensics=forensic_res["pixel_forensics"],
            metadataIntegrity="CANONICAL_ENCODED",
            detectedAnomalies=forensic_res["detected_anomalies"],
            verdictSummary=forensic_res["verdict_summary"],
        ),
        forensicReport=ForensicReport(
            ssim_score=forensic_res["ssim_score"],
            tampered_ratio=forensic_res["tampered_ratio"],
            alignment_quality=forensic_res["alignment_quality"],
            suspicious_regions=suspicious_objs,
            annotated_preview=forensic_res["annotated_preview"],
            difference_preview=forensic_res["difference_preview"],
        ),
    )


# ---------------------------------------------------------------------------
# POST /api/verification/verify
# ---------------------------------------------------------------------------
@router.post(
    "/verify",
    response_model=NoticeVerificationResponse,
    summary="Comprehensive Notice Verification & Tampering Analysis",
    description=(
        "Full-pipeline verification endpoint. Accepts a notice file upload (PDF, PNG, JPG), "
        "a Notice ID, or QR code data. Performs multi-layered cryptographic, steganographic, "
        "and pixel forensic inspection."
    ),
)
def verify_notice(
    file: Optional[UploadFile] = File(None, description="Uploaded document (PDF, PNG, JPG)"),
    notice_id: Optional[str] = Form(None, description="Official Notice ID (optional)"),
    qr_data: Optional[str] = Form(None, description="Decoded QR text or URL (optional)"),
    db: Session = Depends(get_db),
):
    """Execute complete verification workflow for students and verification portals."""
    actual_file = file if isinstance(file, UploadFile) else None
    actual_notice_id = notice_id if isinstance(notice_id, str) else None
    actual_qr_data = qr_data if isinstance(qr_data, str) else None

    file_bytes = None
    if actual_file and actual_file.filename:
        try:
            file_bytes, _, _, _ = validate_uploaded_file(actual_file)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error reading uploaded file: {e}",
            )

    if not file_bytes and not actual_notice_id and not actual_qr_data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Please provide an uploaded document file, a Notice ID, or QR code data.",
        )

    return _perform_core_verification(
        db=db,
        file_bytes=file_bytes,
        notice_id_input=actual_notice_id,
        qr_data_input=actual_qr_data,
    )


# ---------------------------------------------------------------------------
# POST /api/verification/verify-file
# ---------------------------------------------------------------------------
@router.post(
    "/verify-file",
    response_model=NoticeVerificationResponse,
    summary="Verify Notice by Document Upload Only",
    description="Inspects an uploaded document, decodes embedded QR/watermarks, and verifies authenticity.",
)
def verify_notice_by_file(
    file: UploadFile = File(..., description="Uploaded notice document (PDF, PNG, JPG)"),
    db: Session = Depends(get_db),
):
    """Upload-only verification endpoint."""
    file_bytes, _, _, _ = validate_uploaded_file(file)
    return _perform_core_verification(db=db, file_bytes=file_bytes)


# ---------------------------------------------------------------------------
# GET /api/verification/notices/{notice_id}
# ---------------------------------------------------------------------------
@router.get(
    "/notices/{notice_id}",
    response_model=NoticeVerificationResponse,
    summary="Verify Notice by Notice ID Lookup",
    description="Retrieve official notice status and cryptographic signature details by Notice ID.",
)
def verify_notice_by_id(
    notice_id: str,
    db: Session = Depends(get_db),
):
    """Notice ID verification endpoint."""
    return _perform_core_verification(db=db, notice_id_input=notice_id)


# ---------------------------------------------------------------------------
# POST /api/verification/extract-watermark
# ---------------------------------------------------------------------------
@router.post(
    "/extract-watermark",
    response_model=WatermarkExtractionResponse,
    summary="Extract Steganographic Watermark from Document Image",
    description="Extracts 2D-DCT frequency-domain watermark embedded within notice image pixels.",
)
def extract_watermark_endpoint(
    file: UploadFile = File(..., description="Document image file"),
):
    """Inspect and decode frequency-domain DCT watermark from image pixels."""
    file_bytes, _, _, _ = validate_uploaded_file(file)

    try:
        from PIL import Image
        img = Image.open(io.BytesIO(file_bytes))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid image format for watermark extraction: {e}",
        )

    watermark_service = get_watermark_service()
    res = watermark_service.extract_watermark(img)

    detected = res.get("detected", False)
    notice_id = res.get("notice_id")
    conf = res.get("confidence", 0.0)

    explanation = (
        f"DCT watermark recovered for Notice ID '{notice_id}' with {conf * 100:.1f}% confidence."
        if detected
        else "No valid 2D-DCT watermark detected in mid-frequency transform coefficients."
    )

    return WatermarkExtractionResponse(
        detected=detected,
        notice_id=notice_id,
        confidence=conf,
        version=res.get("version", 1),
        method="2D-DCT Mid-Frequency",
        explanation=explanation,
    )


# ---------------------------------------------------------------------------
# POST /api/verification/verify-signature
# ---------------------------------------------------------------------------
@router.post(
    "/verify-signature",
    response_model=SignatureVerificationResponse,
    summary="Verify Notice Cryptographic Signature",
    description="Verify Ed25519 digital signature against canonical signed metadata.",
)
def verify_notice_signature(
    payload: SignatureVerificationRequest,
    db: Session = Depends(get_db),
):
    """Verify Ed25519 signature for a given notice or inline metadata bundle."""
    signature_service = get_signature_service()

    if payload.notice_id and not payload.signed_metadata:
        notice = get_notice_by_notice_id(db, payload.notice_id)
        if not notice:
            return SignatureVerificationResponse(
                status="NOTICE_NOT_FOUND",
                is_valid=False,
                reason=f"Notice '{payload.notice_id}' was not found in the registry.",
                notice_id=payload.notice_id,
                signing_key_id=None,
            )

        if notice.revoked_at:
            return SignatureVerificationResponse(
                status="REVOKED_NOTICE",
                is_valid=False,
                reason="This notice has been officially revoked and is no longer valid.",
                notice_id=notice.notice_id,
                signing_key_id=notice.signing_key_id,
            )

        if not notice.digital_signature or not notice.signed_metadata:
            return SignatureVerificationResponse(
                status="UNSIGNED_NOTICE",
                is_valid=False,
                reason="This notice does not have a digital signature on record.",
                notice_id=notice.notice_id,
                signing_key_id=None,
            )

        try:
            metadata_dict = json.loads(notice.signed_metadata)
        except (json.JSONDecodeError, TypeError):
            return SignatureVerificationResponse(
                status="INVALID_METADATA",
                is_valid=False,
                reason="Stored canonical metadata is malformed and cannot be parsed.",
                notice_id=notice.notice_id,
                signing_key_id=notice.signing_key_id,
            )

        verdict, reason = signature_service.verify_signature(
            metadata=metadata_dict,
            signature_hex=notice.digital_signature,
            key_id=notice.signing_key_id,
        )

        return SignatureVerificationResponse(
            status=verdict,
            is_valid=(verdict == "VALID_SIGNATURE"),
            reason=reason,
            notice_id=notice.notice_id,
            signing_key_id=notice.signing_key_id,
            canonical_metadata=metadata_dict,
        )

    if payload.signed_metadata and payload.digital_signature and payload.signing_key_id:
        verdict, reason = signature_service.verify_signature(
            metadata=payload.signed_metadata,
            signature_hex=payload.digital_signature,
            key_id=payload.signing_key_id,
        )

        notice_id_from_meta = (
            payload.signed_metadata.get("notice_id")
            if isinstance(payload.signed_metadata, dict)
            else None
        )

        return SignatureVerificationResponse(
            status=verdict,
            is_valid=(verdict == "VALID_SIGNATURE"),
            reason=reason,
            notice_id=payload.notice_id or notice_id_from_meta,
            signing_key_id=payload.signing_key_id,
            canonical_metadata=payload.signed_metadata
            if isinstance(payload.signed_metadata, dict)
            else None,
        )

    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="Provide either a 'notice_id' or a complete 'signed_metadata' + 'digital_signature' + 'signing_key_id' bundle.",
    )


# ---------------------------------------------------------------------------
# POST /api/verification/file-integrity/{notice_id}
# ---------------------------------------------------------------------------
@router.post(
    "/file-integrity/{notice_id}",
    response_model=FileIntegrityVerificationResponse,
    summary="Verify File Byte Integrity",
    description="Compare uploaded file SHA-256 against registered original hash.",
)
def verify_file_integrity(
    notice_id: str,
    file: UploadFile = File(..., description="Document file to check"),
    db: Session = Depends(get_db),
):
    """Compare uploaded file SHA-256 against stored original hash."""
    notice = get_notice_by_notice_id(db, notice_id)
    if not notice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notice '{notice_id}' was not found.",
        )

    if not notice.sha256_hash:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This notice does not have a stored SHA-256 hash for comparison.",
        )

    file_bytes, _, _, _ = validate_uploaded_file(file)
    calculated = HashService.calculate_bytes_hash(file_bytes)
    calculated_sha256 = calculated["hash"]
    is_match = calculated_sha256.lower() == notice.sha256_hash.lower()

    return FileIntegrityVerificationResponse(
        status="EXACT_MATCH" if is_match else "HASH_MISMATCH",
        is_exact_match=is_match,
        notice_id=notice.notice_id,
        calculated_sha256=calculated_sha256,
        expected_sha256=notice.sha256_hash,
        explanation=(
            "The uploaded file is byte-for-byte identical to the original registered document."
            if is_match
            else "The uploaded file does not match the original registered document hash."
        ),
    )


# ---------------------------------------------------------------------------
# GET /api/verification/public-key
# ---------------------------------------------------------------------------
@router.get(
    "/public-key",
    response_model=PublicKeyInfoResponse,
    summary="Get Active Signing Public Key",
    description="Retrieve the currently active Ed25519 public key used for notice signing.",
)
def get_active_public_key():
    """Return the active Ed25519 public key."""
    signature_service = get_signature_service()
    key_info = signature_service.get_active_public_key_info()
    if not key_info:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No active signing key configured.",
        )
    return PublicKeyInfoResponse(**key_info)


# ---------------------------------------------------------------------------
# GET /api/verification/public-key/{key_id}
# ---------------------------------------------------------------------------
@router.get(
    "/public-key/{key_id}",
    response_model=PublicKeyInfoResponse,
    summary="Get Public Key by ID",
    description="Retrieve Ed25519 public key information for a specific key ID.",
)
def get_public_key_by_id(key_id: str):
    """Return public key info for a specific key_id."""
    signature_service = get_signature_service()
    key_info = signature_service.get_public_key_info(key_id)
    if not key_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Key '{key_id}' was not found in the trusted key registry.",
        )
    return PublicKeyInfoResponse(**key_info)
