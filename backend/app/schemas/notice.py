"""
Notice Schemas
Defines request and response validation contracts for notices.
Prepares structure for Phase 3 digital signature and verification fields.
"""

from datetime import datetime
from typing import List, Optional
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

    # Extensible Phase 3 Verification Fields (Nullable until Phase 3)
    sha256_hash: Optional[str] = None
    digital_signature: Optional[str] = None
    signing_key_id: Optional[str] = None
    signed_metadata: Optional[str] = None
    revoked_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class NoticeListResponse(BaseModel):
    """Paginated response containing multiple notices."""
    items: List[NoticeResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

