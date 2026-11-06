"""
Verification Schemas
Pydantic data models for student-facing notice verification, image forensics,
watermark recovery, and public key lookups.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SuspiciousRegion(BaseModel):
    """Details of a localized pixel modification detected in document forensics."""
    region_id: str
    location: str
    coordinates: Dict[str, int] = Field(..., description="x, y, w, h bounding box")
    area_pixels: int
    severity: str = Field(..., description="HIGH, MEDIUM, or LOW")
    reason: str


class SecurityAuditDetails(BaseModel):
    """Multi-layer cryptographic, steganographic, and forensic diagnostic matrix."""
    cryptographicSignature: str = Field(
        ..., description="VALID_MATCH, INDIRECT_MATCH, INVALID, or UNSIGNED"
    )
    signatureAlgorithm: str = "Ed25519"
    watermarkIntegrity: str = Field(
        ..., description="INTACT, DEGRADED_BY_COMPRESSION, or ABSENT"
    )
    watermarkDetected: bool = False
    pixelForensics: str = Field(
        ..., description="CLEAN_NO_ALTERATION, JPEG_COMPRESSION_ARTIFACTS_ONLY, or LOCALIZED_TAMPERING_DETECTED"
    )
    metadataIntegrity: str = "CANONICAL_ENCODED"
    detectedAnomalies: List[str] = Field(default_factory=list)
    verdictSummary: str


class ForensicReport(BaseModel):
    """Detailed forensic analysis report for student and auditor inspection."""
    ssim_score: float
    tampered_ratio: float
    alignment_quality: str
    suspicious_regions: List[SuspiciousRegion] = Field(default_factory=list)
    annotated_preview: Optional[str] = None
    difference_preview: Optional[str] = None


class NoticeVerificationResponse(BaseModel):
    """
    Standard verification response payload compatible with both the React frontend
    and automated verification clients.
    """
    status: str = Field(
        ...,
        description="VERIFIED, AUTHENTIC_TRANSFORMED, TAMPERING_DETECTED, or UNVERIFIABLE",
    )
    id: Optional[str] = None
    notice_id: Optional[str] = None
    title: Optional[str] = None
    department: Optional[str] = None
    issuer: Optional[str] = None
    issueDate: Optional[str] = None
    published_at: Optional[str] = None
    matchScore: int = Field(0, description="Confidence score from 0 to 100")
    contentSnippet: Optional[str] = None
    original_sha256: Optional[str] = None
    uploaded_sha256: Optional[str] = None
    sha256_match: bool = False
    signature_valid: bool = False
    watermark_recovered: bool = False
    securityAudit: SecurityAuditDetails
    forensicReport: Optional[ForensicReport] = None


class WatermarkExtractionResponse(BaseModel):
    """Response returned when querying watermark recovery on an uploaded document."""
    detected: bool
    notice_id: Optional[str] = None
    confidence: float
    version: int = 1
    method: str = "2D-DCT Mid-Frequency"
    explanation: str

