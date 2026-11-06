"""
Notice Model
Represents official college notices issued by administrators.
Includes pre-planned Phase 3 cryptographic verification fields.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Notice(Base):
    """Official College Notice entity."""

    __tablename__ = "notices"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    # Unique institutional Notice ID, e.g. FS-GMU-2026-A8F29C
    notice_id = Column(String(64), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=False, default="General")

    # File storage metadata
    original_filename = Column(String(255), nullable=False)
    stored_file_path = Column(String(512), nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)  # in bytes

    # Administrative provenance
    issuer_admin_id = Column(
        String(36),
        ForeignKey("admins.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    publication_status = Column(
        String(20),
        default="published",
        nullable=False,
        index=True,
    )  # draft, published, archived

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # --------------------------------------------------------------------------
    # Phase 3 Cryptographic Extensibility Fields (Nullable in Phase 2)
    # --------------------------------------------------------------------------
    sha256_hash = Column(String(64), nullable=True, index=True)
    digital_signature = Column(Text, nullable=True)
    signing_key_id = Column(String(100), nullable=True)
    signed_metadata = Column(Text, nullable=True)  # JSON-encoded payload
    revoked_at = Column(DateTime(timezone=True), nullable=True)

    # Relationship to issuing administrator
    issuer_admin = relationship("Admin", back_populates="notices")

    def __repr__(self) -> str:
        return f"<Notice notice_id={self.notice_id} title='{self.title[:30]}' status={self.publication_status}>"

