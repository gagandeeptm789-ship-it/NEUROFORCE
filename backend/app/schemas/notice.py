"""
Notice Schemas
Defines request and response validation contracts for notices,
including Phase 3 digital signature and Phase 4 secure publishing fields.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class NoticeBase(BaseModel):
    """Base notice attributes."""
    title: str = Field(..., min_length=3, max_length=255, description="Headline/Title of the notice")
    description: Optional[str] = Field(None, max_length=10000, description="Full description or summary")
    category: str = Field("General", min_length=2, max_length=100, description="Category: Academic, Exam, etc.")
    publication_status: str = Field("published", description="Status: draft, published, archived")


class NoticeStatusUpdate(BaseModel):
    """Payload for updating publication status of a notice."""
    publication_status: str = Field(
        ...,
        pattern="^(draft|published|archived)$",
        description="Allowed statuses: draft, published, archived",
    )


class AdminBrief(BaseModel):
    """Concise representation of issuing administrator."""
    id: str
    full_name: str
    email: str
    role: str

    model_config = ConfigDict(from_attributes=True)


class NoticeResponse(BaseModel):
    """Full public representation of an official notice."""
    id: str
    notice_id: str
    title: str
    description: Optional[str] = None
    category: str
    original_filename: str
    mime_type: str
    file_size: int
    publication_status: str
    issuer_admin_id: str
    created_at: datetime
    updated_at: datetime

    # Associated issuer details (optional eager load)
    issuer_admin: Optional[AdminBrief] = None

    # Download URL endpoint helper
    file_download_url: Optional[str] = None

    # Phase 3 Cryptographic Verification Fields
    sha256_hash: Optional[str] = None
    hash_algorithm: Optional[str] = "SHA-256"
    digital_signature: Optional[str] = None
    signature_algorithm: Optional[str] = "Ed25519"
    signing_key_id: Optional[str] = None
    signed_metadata: Optional[str] = None
    metadata_version: Optional[str] = "1.0"
    signed_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None

    # Phase 4 Secure Publishing & Distribution Fields
    distribution_status: Optional[str] = "DRAFT"
    qr_code_url: Optional[str] = None
    verification_url: Optional[str] = None
    published_file_url: Optional[str] = None
    watermark_version: Optional[str] = None
    watermark_reference: Optional[str] = None
    publication_timestamp: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class NoticeListResponse(BaseModel):
    """Paginated response containing multiple notices."""
    items: List[NoticeResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    stats: Optional["NoticeDashboardStats"] = None


class NoticeDashboardStats(BaseModel):
    """Persisted dashboard counts; audit counts remain absent until audit storage exists."""
    total_notices: int
    published_notices: int
    flagged_tampered_attempts: Optional[int] = None
    active_verifications_today: Optional[int] = None


class SignatureVerificationRequest(BaseModel):
    """Request payload for signature verification."""
    notice_id: Optional[str] = None
    signed_metadata: Optional[Dict[str, Any]] = None
    digital_signature: Optional[str] = None
    signing_key_id: Optional[str] = None


class SignatureVerificationResponse(BaseModel):
    """Detailed cryptographic signature verification verdict."""
    status: str  # VALID_SIGNATURE, INVALID_SIGNATURE, UNKNOWN_KEY, REVOKED_KEY, NOTICE_NOT_FOUND, INVALID_METADATA
    is_valid: bool
    reason: Optional[str] = None
    notice_id: Optional[str] = None
    signing_key_id: Optional[str] = None
    algorithm: str = "Ed25519"
    canonical_metadata: Optional[Dict[str, Any]] = None


class FileIntegrityVerificationResponse(BaseModel):
    """File byte-exact integrity check verdict."""
    status: str  # EXACT_MATCH, HASH_MISMATCH, NOTICE_NOT_FOUND
    is_exact_match: bool
    notice_id: str
    calculated_sha256: str
    expected_sha256: Optional[str] = None
    explanation: str


class PublishNoticeResponse(BaseModel):
    """Confirmation of notice distribution publishing."""
    notice_id: str
    distribution_status: str
    qr_code_url: str
    verification_url: str
    published_file_url: str
    watermark_reference: Optional[str] = None
    publication_timestamp: datetime


class PublicKeyInfoResponse(BaseModel):
    """Trusted public key entry."""
    key_id: str
    algorithm: str = "Ed25519"
    public_key_hex: str
    public_key_pem: str
    status: str  # active, revoked
    created_at: str
    revoked_at: Optional[str] = None


class WatermarkInfoResponse(BaseModel):
    """Diagnostics for embedded digital watermark."""
    notice_id: str
    watermark_version: str
    watermark_reference: str
    method: str
    embedded: bool
    description: str
