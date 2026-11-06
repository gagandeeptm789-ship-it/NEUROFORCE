"""
PDF Publishing Service
Generates authentic distribution copies of PDF notices with official QR verification stamps.
Preserves original uploaded files, maintains vector and text searchability without rasterization.
"""

import io
import logging
import os
from typing import Optional, Tuple

from PIL import Image, ImageDraw, ImageFont
import pypdf

from app.core.config import get_settings
from app.services.qr_service import QRService, get_qr_service

logger = logging.getLogger("forwarded_seal.pdf_publishing")
settings = get_settings()


class PDFPublishingService:
    """Service for producing published PDF distribution copies with QR verification stamps."""

    def __init__(
        self,
        published_dir: Optional[str] = None,
        qr_service: Optional[QRService] = None,
    ):
        if published_dir:
            self.published_dir = published_dir
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.published_dir = os.path.join(base_dir, settings.PUBLISHED_DIR)

        os.makedirs(self.published_dir, exist_ok=True)
        self.qr_service = qr_service or get_qr_service()

    def create_official_qr_stamp_image(
        self,
        notice_id: str,
        verification_url: str,
    ) -> Image.Image:
        """
        Create a crisp institutional verification seal card containing the QR code,
        institution brand, and Notice ID identifier.
        """
        qr_png_bytes = self.qr_service.generate_qr_image_bytes(
            notice_id=notice_id,
            verification_url=verification_url,
            box_size=4,
            border=2,
        )
        qr_img = Image.open(io.BytesIO(qr_png_bytes)).convert("RGB")
        qr_w, qr_h = qr_img.size

        card_w = qr_w + 30
        card_h = qr_h + 46

        stamp = Image.new("RGB", (card_w, card_h), color=(255, 255, 255))
        draw = ImageDraw.Draw(stamp)

        # Border
        draw.rectangle([0, 0, card_w - 1, card_h - 1], outline=(15, 23, 42), width=2)
        # Header bar
        draw.rectangle([0, 0, card_w - 1, 16], fill=(11, 17, 32))

        # Title text
        draw.text((6, 2), "THE FORWARDED SEAL", fill=(0, 229, 255))

        # Paste QR
        stamp.paste(qr_img, (15, 20))

        # Footer Notice ID
        draw.text((10, card_h - 22), "VERIFY SOURCE QR", fill=(100, 116, 139))
        draw.text((10, card_h - 12), notice_id[:24], fill=(15, 23, 42))

        return stamp

    def generate_published_pdf(
        self,
        original_pdf_path: str,
        notice_id: str,
        verification_url: str,
        output_pdf_path: Optional[str] = None,
    ) -> str:
        """
        Generate a distribution copy of a PDF notice with the verification QR stamp.
        Preserves the original PDF and maintains searchable vector text.
        """
        if not os.path.exists(original_pdf_path):
            raise FileNotFoundError(f"Original PDF not found: {original_pdf_path}")

        reader = pypdf.PdfReader(original_pdf_path)
        writer = pypdf.PdfWriter()

        if len(reader.pages) == 0:
            raise ValueError("Input PDF contains no pages.")

        # 1. Build stamp image and convert to overlay PDF page
        stamp_img = self.create_official_qr_stamp_image(notice_id, verification_url)
        stamp_pdf_io = io.BytesIO()
        stamp_img.save(stamp_pdf_io, format="PDF")
        stamp_pdf_io.seek(0)

        stamp_reader = pypdf.PdfReader(stamp_pdf_io)
        stamp_page = stamp_reader.pages[0]

        # 2. Iterate pages and apply stamp to the first page
        for i, page in enumerate(reader.pages):
            if i == 0:
                # Target stamp size ~90x110 points
                page_w = float(page.mediabox.width)
                page_h = float(page.mediabox.height)

                stamp_w = float(stamp_page.mediabox.width)
                stamp_h = float(stamp_page.mediabox.height)

                target_w = 95.0
                scale = target_w / stamp_w
                scaled_h = stamp_h * scale

                # Position in bottom-right margin with 15pt padding
                tx = page_w - target_w - 20.0
                ty = 20.0

                # Transformation matrix [scale, 0, 0, scale, tx, ty]
                stamp_page.add_transformation(
                    pypdf.Transformation().scale(scale).translate(tx=tx, ty=ty)
                )
                page.merge_page(stamp_page)

            writer.add_page(page)

        # 3. Save distribution copy
        if not output_pdf_path:
            clean_id = notice_id.replace("/", "_").replace(":", "_")
            output_pdf_path = os.path.join(self.published_dir, f"{clean_id}_published.pdf")

        with open(output_pdf_path, "wb") as f_out:
            writer.write(f_out)

        logger.info(
            "Generated published distribution PDF for '%s' at '%s'",
            notice_id,
            output_pdf_path,
        )
        return output_pdf_path


# Singleton instance
_pdf_service_instance: Optional[PDFPublishingService] = None


def get_pdf_publishing_service() -> PDFPublishingService:
    """Return shared PDFPublishingService singleton."""
    global _pdf_service_instance
    if _pdf_service_instance is None:
        _pdf_service_instance = PDFPublishingService()
    return _pdf_service_instance

