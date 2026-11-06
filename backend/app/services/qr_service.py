"""
QR Code Generation Service
Generates official optical verification QR codes for notices using high error correction.
Points directly to the public verification URL for the specific Notice ID.
"""

import io
import logging
import os
from typing import Optional, Tuple

import qrcode
from qrcode.constants import ERROR_CORRECT_H

from app.core.config import get_settings

logger = logging.getLogger("forwarded_seal.qr")
settings = get_settings()


class QRService:
    """Service for generating and managing notice verification QR codes."""

    def __init__(self, qr_dir: Optional[str] = None):
        if qr_dir:
            self.qr_dir = qr_dir
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.qr_dir = os.path.join(base_dir, settings.QR_DIR)

        os.makedirs(self.qr_dir, exist_ok=True)

    def build_verification_url(self, notice_id: str) -> str:
        """
        Build the official canonical verification URL for a given Notice ID.
        Example: http://localhost:3000/verify/FS-GMU-2026-A8F29C
        """
        base_url = settings.PUBLIC_VERIFICATION_BASE_URL.rstrip("/")
        clean_id = notice_id.strip()
        return f"{base_url}/{clean_id}"

    def generate_qr_image_bytes(
        self,
        notice_id: str,
        verification_url: Optional[str] = None,
        box_size: int = 10,
        border: int = 4,
    ) -> bytes:
        """
        Generate raw PNG bytes of the QR code using High (H) error correction.
        """
        url = verification_url or self.build_verification_url(notice_id)

        qr = qrcode.QRCode(
            version=None,  # Auto-determine smallest fit
            error_correction=ERROR_CORRECT_H,
            box_size=box_size,
            border=border,
        )
        qr.add_data(url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    def generate_qr_code(
        self,
        notice_id: str,
        verification_url: Optional[str] = None,
    ) -> Tuple[str, str]:
        """
        Generate and persist QR code PNG file to disk.
        Returns:
            (stored_qr_path, verification_url)
        """
        url = verification_url or self.build_verification_url(notice_id)
        png_bytes = self.generate_qr_image_bytes(notice_id, url)

        filename = f"{notice_id.replace('/', '_').replace(':', '_')}_qr.png"
        file_path = os.path.join(self.qr_dir, filename)

        with open(file_path, "wb") as f:
            f.write(png_bytes)

        logger.info("Generated high-res QR code for notice '%s' at '%s'", notice_id, file_path)
        return file_path, url


# Singleton instance
_qr_service_instance: Optional[QRService] = None


def get_qr_service() -> QRService:
    """Return shared QRService singleton."""
    global _qr_service_instance
    if _qr_service_instance is None:
        _qr_service_instance = QRService()
    return _qr_service_instance

