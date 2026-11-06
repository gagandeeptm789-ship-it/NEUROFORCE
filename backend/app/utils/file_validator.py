"""
File Validation Utilities
Validates uploaded documents for university notices.
Inspects actual binary content headers (magic bytes), file extensions,
sanitizes filenames, and prevents path traversal attacks.
"""

import os
import re
from typing import Dict, Optional, Tuple
from fastapi import HTTPException, UploadFile, status

from app.core.config import get_settings

settings = get_settings()

# Allowed file extensions mapped to expected MIME types and binary magic signatures
ALLOWED_EXTENSIONS: Dict[str, Dict[str, any]] = {
    ".pdf": {
        "mime_type": "application/pdf",
        "magic_bytes": [b"%PDF-"],
        "description": "Portable Document Format (PDF)",
    },
    ".png": {
        "mime_type": "image/png",
        "magic_bytes": [b"\x89PNG\r\n\x1a\n"],
        "description": "Portable Network Graphics (PNG)",
    },
    ".jpg": {
        "mime_type": "image/jpeg",
        "magic_bytes": [b"\xff\xd8\xff"],
        "description": "JPEG Image",
    },
    ".jpeg": {
        "mime_type": "image/jpeg",
        "magic_bytes": [b"\xff\xd8\xff"],
        "description": "JPEG Image",
    },
}


def sanitize_filename(filename: str) -> str:
    """
    Sanitize an uploaded filename:
    - Removes path components (preventing path traversal).
    - Removes control characters and unsafe symbols.
    - Limits name length.
    """
    if not filename:
        return "unnamed_document"

    # Extract base name only (strip any directory slashes)
    clean_name = os.path.basename(filename)
    # Remove null bytes
    clean_name = clean_name.replace("\x00", "")
    # Replace whitespace and unsafe characters with underscores
    clean_name = re.sub(r"[^\w.\-]", "_", clean_name)
    # Limit to reasonable length
    if len(clean_name) > 200:
        base, ext = os.path.splitext(clean_name)
        clean_name = base[: 200 - len(ext)] + ext
    return clean_name or "document"


def validate_file_magic_bytes(header: bytes, extension: str) -> bool:
    """
    Inspect the binary header (first 16-32 bytes) against known signatures.
    """
    spec = ALLOWED_EXTENSIONS.get(extension.lower())
    if not spec:
        return False

    for magic in spec["magic_bytes"]:
        if header.startswith(magic):
            return True
    return False


def validate_uploaded_file(file: UploadFile) -> Tuple[bytes, str, str, int]:
    """
    Thoroughly inspect and validate an uploaded document.
    Returns:
        (file_bytes, sanitized_filename, detected_mime_type, file_size)
    Raises:
        HTTPException(400) if validation fails.
    """
    if not file or not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A file attachment is required to create a notice.",
        )

    # 1. Sanitize original filename
    clean_filename = sanitize_filename(file.filename)
    _, ext = os.path.splitext(clean_filename)
    ext = ext.lower()

    if ext not in ALLOWED_EXTENSIONS:
        allowed_list = ", ".join(ALLOWED_EXTENSIONS.keys())
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{ext}'. Allowed formats: {allowed_list}",
        )

    # 2. Read file content safely with size limit checking
    max_size = settings.MAX_UPLOAD_SIZE_BYTES
    raw_file = getattr(file, "file", file)
    if hasattr(raw_file, "read"):
        file_bytes = raw_file.read()
    else:
        file_bytes = b""

    total_bytes = len(file_bytes)
    if total_bytes > max_size:
        max_mb = max_size / (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds maximum allowed size of {max_mb:.1f} MB.",
        )

    if total_bytes == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is empty (0 bytes).",
        )

    # 3. Validate actual binary magic bytes (deep content inspection)
    header = file_bytes[:16]
    if not validate_file_magic_bytes(header, ext):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"File content does not match genuine {ext.upper()} format. "
                "Disguised or corrupted files are strictly rejected."
            ),
        )

    detected_mime = ALLOWED_EXTENSIONS[ext]["mime_type"]
    return file_bytes, clean_filename, detected_mime, total_bytes
