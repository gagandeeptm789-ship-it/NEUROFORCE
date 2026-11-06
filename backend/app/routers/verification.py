"""
Verification Router
Public endpoints for cryptographic signature verification, file integrity checking,
and trusted public key retrieval for The Forwarded Seal platform.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.notice import (
    FileIntegrityVerificationResponse,
    PublicKeyInfoResponse,
    SignatureVerificationRequest,
    SignatureVerificationResponse,
)
from app.services.hash_service import HashService
from app.services.notice_service import get_notice_by_notice_id
from app.services.signature_service import get_signature_service
from app.utils.file_validator import validate_uploaded_file

import json

logger = logging.getLogger("forwarded_seal.verification_router")

router = APIRouter(prefix="/verification", tags=["Cryptographic Verification"])


# ---------------------------------------------------------------------------
# POST /api/verification/verify-signature
# ---------------------------------------------------------------------------
@router.post(
    "/verify-signature",
    response_model=SignatureVerificationResponse,
    summary="Verify Notice Cryptographic Signature",
    description=(
        "Verify the Ed25519 digital signature of an official notice. "
        "Accepts either a Notice ID (for server-side lookup) or an inline "
        "signed_metadata + digital_signature + signing_key_id triple."
    ),
)
def verify_notice_signature(
    payload: SignatureVerificationRequest,
    db: Session = Depends(get_db),
):
    """Verify Ed25519 signature for a given notice or inline metadata bundle."""
    signature_service = get_signature_service()

    # -- Case 1: Caller provides a Notice ID → fetch from DB --
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

    # -- Case 2: Caller provides inline metadata bundle --
    if payload.signed_metadata and payload.digital_signature and payload.signing_key_id:
        verdict, reason = signature_service.verify_signature(
            metadata=payload.signed_metadata,
            signature_hex=payload.digital_signature,
            key_id=payload.signing_key_id,
        )

        notice_id_from_meta = payload.signed_metadata.get("notice_id") if isinstance(payload.signed_metadata, dict) else None

        return SignatureVerificationResponse(
            status=verdict,
            is_valid=(verdict == "VALID_SIGNATURE"),
            reason=reason,
            notice_id=payload.notice_id or notice_id_from_meta,
            signing_key_id=payload.signing_key_id,
            canonical_metadata=payload.signed_metadata if isinstance(payload.signed_metadata, dict) else None,
        )

    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=(
            "Provide either a 'notice_id' for server-side lookup, or a complete "
            "'signed_metadata' + 'digital_signature' + 'signing_key_id' bundle."
        ),
    )


# ---------------------------------------------------------------------------
# POST /api/verification/file-integrity/{notice_id}
# ---------------------------------------------------------------------------
@router.post(
    "/file-integrity/{notice_id}",
    response_model=FileIntegrityVerificationResponse,
    summary="Verify File Byte Integrity",
    description=(
        "Upload a copy of a notice document and verify whether it is byte-for-byte "
        "identical to the original registered file. A HASH_MISMATCH indicates the file "
        "has been altered or re-compressed but does NOT by itself prove forgery."
    ),
)
def verify_file_integrity(
    notice_id: str,
    file: UploadFile = File(..., description="The notice document file to check (PDF, PNG, JPG)"),
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

    # Read and hash the uploaded file
    try:
        file_bytes, _, _, _ = validate_uploaded_file(file)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not read uploaded file: {e}",
        )

    calculated = HashService.calculate_bytes_hash(file_bytes)
    calculated_sha256 = calculated["hash"]

    is_match = (calculated_sha256.lower() == notice.sha256_hash.lower())

    if is_match:
        result_status = "EXACT_MATCH"
        explanation = (
            "The uploaded file is byte-for-byte identical to the original registered document. "
            "File integrity is confirmed."
        )
    else:
        result_status = "HASH_MISMATCH"
        explanation = (
            "The uploaded file does not match the original registered document hash. "
            "This may indicate the file was re-saved, re-compressed, forwarded via a lossy "
            "channel, or manually modified. HASH_MISMATCH alone does not prove forgery — "
            "use Signature Verification for authenticity proof."
        )

    return FileIntegrityVerificationResponse(
        status=result_status,
        is_exact_match=is_match,
        notice_id=notice.notice_id,
        calculated_sha256=calculated_sha256,
        expected_sha256=notice.sha256_hash,
        explanation=explanation,
    )


# ---------------------------------------------------------------------------
# GET /api/verification/public-key
# ---------------------------------------------------------------------------
@router.get(
    "/public-key",
    response_model=PublicKeyInfoResponse,
    summary="Get Active Signing Public Key",
    description=(
        "Retrieve the currently active Ed25519 public key used for notice signing. "
        "Use this key to independently verify notice signatures."
    ),
)
def get_active_public_key():
    """Return the active Ed25519 public key."""
    signature_service = get_signature_service()
    key_info = signature_service.get_active_public_key_info()
    if not key_info:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No active signing key is configured. Please contact the system administrator.",
        )
    return PublicKeyInfoResponse(**key_info)


# ---------------------------------------------------------------------------
# GET /api/verification/public-key/{key_id}
# ---------------------------------------------------------------------------
@router.get(
    "/public-key/{key_id}",
    response_model=PublicKeyInfoResponse,
    summary="Get Public Key by ID",
    description=(
        "Retrieve Ed25519 public key information for a specific key ID. "
        "Returns key status (active or revoked) and PEM-encoded public key."
    ),
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

