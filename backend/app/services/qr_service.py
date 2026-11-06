"""
QR Code Generation & Optical Decoding Service
Generates official optical verification QR codes for notices using high error correction.
Decodes QR codes from uploaded images and document pages.
Supports native OpenCV QRCodeEncoder/Detector with optional fallback to python-qrcode.
"""

import io
import logging
import os
from typing import Optional, Tuple, Union

import cv2
import numpy as np
from PIL import Image

try:
    import qrcode
    from qrcode.constants import ERROR_CORRECT_H
    _HAS_QRCODE_LIB = True
except ImportError:
    _HAS_QRCODE_LIB = False

from app.core.config import get_settings

logger = logging.getLogger("forwarded_seal.qr")
settings = get_settings()


class QRService:
    """Service for generating, managing, and decoding notice verification QR codes."""

    def __init__(self, qr_dir: Optional[str] = None):
        if qr_dir:
            self.qr_dir = qr_dir
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.qr_dir = os.path.join(base_dir, settings.QR_DIR)

        os.makedirs(self.qr_dir, exist_ok=True)
        self.detector = cv2.QRCodeDetector()

    def build_verification_url(self, notice_id: str) -> str:
        """
        Build the official canonical verification URL for a given Notice ID.
        Example: http://localhost:3000/verify/FS-GMU-2026-A8F29C
        """
        base_url = settings.PUBLIC_VERIFICATION_BASE_URL.rstrip("/")
        clean_id = notice_id.strip()
        return f"{base_url}/{clean_id}"

    def extract_notice_id_from_url_or_text(self, qr_text: str) -> Optional[str]:
        """
        Extract the Notice ID from a scanned QR payload (URL or plain ID).
        Example: 'http://localhost:3000/verify/FS-GMU-2026-A8F29C' -> 'FS-GMU-2026-A8F29C'
        """
        if not qr_text:
            return None
        clean = qr_text.strip()
        if "/verify/" in clean:
            return clean.split("/verify/")[-1].split("?")[0].strip()
        if clean.startswith("FS-"):
            return clean.split("?")[0].strip()
        return clean

    def generate_qr_image_bytes(
        self,
        notice_id: str,
        verification_url: Optional[str] = None,
        box_size: int = 10,
        border: int = 4,
    ) -> bytes:
        """
        Generate raw PNG bytes of the QR code using High error correction.
        """
        url = verification_url or self.build_verification_url(notice_id)

        if _HAS_QRCODE_LIB:
            try:
                qr = qrcode.QRCode(
                    version=None,
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
            except Exception as e:
                logger.warning("qrcode lib failed, falling back to OpenCV: %s", e)

        # Native OpenCV QRCodeEncoder fallback
        encoder = cv2.QRCodeEncoder.create()
        matrix = encoder.encode(url)
        # Pad with white border
        padded = np.pad(matrix, border, mode="constant", constant_values=255)
        # Scale up
        target_w = padded.shape[1] * box_size
        target_h = padded.shape[0] * box_size
        scaled = cv2.resize(padded, (target_w, target_h), interpolation=cv2.INTER_NEAREST)
        success, buf = cv2.imencode(".png", scaled)
        if not success:
            raise RuntimeError("Failed to encode QR image bytes via OpenCV.")
        return buf.tobytes()

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

    def decode_qr_from_image(
        self,
        image_input: Union[str, bytes, np.ndarray, Image.Image],
    ) -> Optional[str]:
        """
        Detect and decode a QR code from an image (filepath, raw bytes, OpenCV array, or PIL Image).
        Returns decoded text/URL or None if no QR detected.
        """
        try:
            cv_img = None
            if isinstance(image_input, (str, os.PathLike)):
                if not os.path.exists(image_input):
                    return None
                cv_img = cv2.imread(str(image_input))
            elif isinstance(image_input, bytes):
                nparr = np.frombuffer(image_input, np.uint8)
                cv_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            elif isinstance(image_input, Image.Image):
                cv_img = cv2.cvtColor(np.array(image_input), cv2.COLOR_RGB2BGR)
            elif isinstance(image_input, np.ndarray):
                cv_img = image_input

            if cv_img is None or cv_img.size == 0:
                return None

            # Attempt 1: Direct detection on standard image
            data, bbox, _ = self.detector.detectAndDecode(cv_img)
            if data and data.strip():
                return data.strip()

            # Attempt 2: Grayscale + Histogram Equalization for degraded/screen photo scans
            gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY) if len(cv_img.shape) == 3 else cv_img
            equalized = cv2.equalizeHist(gray)
            data, bbox, _ = self.detector.detectAndDecode(equalized)
            if data and data.strip():
                return data.strip()

            # Attempt 3: Multi-detector detection
            ok, decoded_info, _, _ = self.detector.detectAndDecodeMulti(cv_img)
            if ok and decoded_info:
                for text in decoded_info:
                    if text and text.strip():
                        return text.strip()

            return None
        except Exception as e:
            logger.debug("QR detection attempt failed: %s", e)
            return None


# Singleton instance
_qr_service_instance: Optional[QRService] = None


def get_qr_service() -> QRService:
    """Return shared QRService singleton."""
    global _qr_service_instance
    if _qr_service_instance is None:
        _qr_service_instance = QRService()
    return _qr_service_instance
