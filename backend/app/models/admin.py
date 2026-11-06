"""
Admin Model
Represents authorized college administrators who can issue and manage notices.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.orm import relationship

from app.database import Base


class Admin(Base):
    """Administrator user entity."""

    __tablename__ = "admins"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    full_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="admin", nullable=False)  # super_admin, admin, exam_cell, etc.
    is_active = Column(Boolean, default=True, nullable=False)
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

    # Relationship to notices issued by this administrator
    notices = relationship(
        "Notice",
        back_populates="issuer_admin",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Admin id={self.id} email={self.email} role={self.role} active={self.is_active}>"

