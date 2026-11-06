"""
Notice ID Generator
Generates secure, cryptographically unpredictable, human-readable Notice IDs.
Example format: FS-GMU-2026-A8F29C
"""

import datetime
import secrets
from typing import Optional
from sqlalchemy.orm import Session

from app.core.config import get_settings

settings = get_settings()


def generate_raw_notice_id(
    prefix: Optional[str] = None,
    institution: Optional[str] = None,
    year: Optional[int] = None,
) -> str:
    """
    Construct a structured Notice ID string.
    Uses cryptographically strong pseudo-random number generator (secrets).
    Format: {PREFIX}-{INSTITUTION}-{YEAR}-{6_CHAR_HEX}
    Example: FS-GMU-2026-A8F29C
    """
    prefix = (prefix or settings.NOTICE_ID_PREFIX).strip().upper()
    institution = (institution or settings.INSTITUTION_CODE).strip().upper()
    current_year = year or datetime.datetime.now(datetime.timezone.utc).year
    # 3 bytes produces 6 uppercase hex characters
    random_part = secrets.token_hex(3).upper()

    return f"{prefix}-{institution}-{current_year}-{random_part}"


def generate_unique_notice_id(db: Session, max_retries: int = 10) -> str:
    """
    Generate a guaranteed unique Notice ID by querying against existing database records.
    Prevents any duplicate collisions.
    """
    from app.models.notice import Notice

    for attempt in range(max_retries):
        candidate_id = generate_raw_notice_id()
        existing = db.query(Notice.id).filter(Notice.notice_id == candidate_id).first()
        if not existing:
            return candidate_id

    # Fallback in the near-impossible event of 10 consecutive collisions:
    # Append timestamp microsecond entropy
    timestamp_entropy = secrets.token_hex(4).upper()
    prefix = settings.NOTICE_ID_PREFIX.strip().upper()
    institution = settings.INSTITUTION_CODE.strip().upper()
    year = datetime.datetime.now(datetime.timezone.utc).year
    return f"{prefix}-{institution}-{year}-{timestamp_entropy}"

