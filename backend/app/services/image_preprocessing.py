"""
Image Preprocessing Service
Handles loading, normalization, deskewing, noise filtering, and contrast enhancement
for document images and PDFs during authenticity verification.
"""

import io
import logging
import os
from typing import Any, Dict, Optional, Tuple, Union

import cv2
import numpy as np
from PIL import Image
import pypdf

logger = logging.getLogger("forwarded_seal.image_preprocessing")


class ImagePreprocessingService:
    """Service for robust preprocessing of document images and PDF circulars."""

    @staticmethod
    def load_document_image(
        input_source: Union[bytes, str, os.PathLike, Image.Image, np.ndarray],
        max_dimension: int = 2400,
    ) -> Tuple[np.ndarray, Optional[str]]:
        """
        Load any document source (PDF, PNG, JPG, JPEG, WEBP, numpy array, PIL Image)
        into a standard BGR numpy array and extract any available text.

        Returns:
            Tuple of (bgr_image_array, extracted_text)
        """
        extracted_text = None

        # Case 1: Already a numpy array
        if isinstance(input_source, np.ndarray):
            img = input_source.copy()
            if len(img.shape) == 2:
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            return img, None

        # Case 2: PIL Image
        if isinstance(input_source, Image.Image):
            rgb = input_source.convert("RGB")
            bgr = cv2.cvtColor(np.array(rgb), cv2.COLOR_RGB2BGR)
            return bgr, None

        # Case 3: File path
        if isinstance(input_source, (str, os.PathLike)):
            file_path = str(input_source)
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Document file not found: {file_path}")

            with open(file_path, "rb") as f:
                file_bytes = f.read()
        elif isinstance(input_source, bytes):
            file_bytes = input_source
        else:
            raise ValueError(f"Unsupported document input type: {type(input_source)}")

        # Check if PDF
        if file_bytes.startswith(b"%PDF"):
            return ImagePreprocessingService._load_pdf_as_image(file_bytes, max_dimension)

        # Standard raster image decoding
        nparr = np.frombuffer(file_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            # Fallback to PIL
            try:
                pil_img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
                img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            except Exception as e:
                raise ValueError(f"Failed to decode image data: {e}")

        # Limit maximum dimension to prevent memory exhaustion on extreme uploads
        h, w = img.shape[:2]
        if max(h, w) > max_dimension:
            scale = max_dimension / float(max(h, w))
            img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

        return img, None

    @staticmethod
    def _load_pdf_as_image(
        pdf_bytes: bytes,
        max_dimension: int = 2400,
    ) -> Tuple[np.ndarray, Optional[str]]:
        """
        Process a PDF document: extract embedded images or synthesize a high-contrast
        raster view from page content along with text extraction.
        """
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        if len(reader.pages) == 0:
            raise ValueError("PDF document contains no pages.")

        first_page = reader.pages[0]
        extracted_text = first_page.extract_text() or ""

        # Check if first page has an embedded image
        if hasattr(first_page, "images") and len(first_page.images) > 0:
            try:
                img_obj = first_page.images[0]
                img_bytes = img_obj.data
                nparr = np.frombuffer(img_bytes, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if img is not None:
                    h, w = img.shape[:2]
                    if max(h, w) > max_dimension:
                        scale = max_dimension / float(max(h, w))
                        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
                    return img, extracted_text
            except Exception as e:
                logger.debug("Could not extract raw embedded PDF image: %s", e)

        # If no extractable image or text-only PDF, synthesize a clean canvas representation
        # using PIL with the extracted text to allow visual feature comparison.
        width, height = 1200, 1600
        canvas = Image.new("RGB", (width, height), color=(255, 255, 255))
        from PIL import ImageDraw
        draw = ImageDraw.Draw(canvas)

        # Draw header
        draw.rectangle([40, 40, width - 40, 120], fill=(240, 245, 255), outline=(30, 41, 59), width=2)
        draw.text((60, 65), "OFFICIAL UNIVERSITY CIRCULAR (VECTOR PDF)", fill=(15, 23, 42))

        # Draw lines of text
        y = 160
        for line in extracted_text.splitlines()[:50]:
            clean_line = line.strip()
            if clean_line:
                draw.text((60, y), clean_line[:100], fill=(30, 41, 59))
                y += 24
                if y > height - 100:
                    break

        bgr = cv2.cvtColor(np.array(canvas), cv2.COLOR_RGB2BGR)
        return bgr, extracted_text

    @staticmethod
    def preprocess_image(
        img: np.ndarray,
        apply_deskew: bool = True,
        apply_clahe: bool = True,
        denoise: bool = True,
    ) -> Dict[str, Any]:
        """
        Normalize and enhance a document image:
        - Grayscale conversion
        - Optional deskewing
        - Noise reduction
        - Contrast normalization (CLAHE)

        Returns a dictionary with processed representations and metadata.
        """
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            bgr = img.copy()
        else:
            gray = img.copy()
            bgr = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

        skew_angle = 0.0
        if apply_deskew:
            gray, bgr, skew_angle = ImagePreprocessingService.deskew_image(gray, bgr)

        filtered = gray
        if denoise:
            # Gentle Gaussian filter to suppress high-frequency sensor noise
            filtered = cv2.GaussianBlur(gray, (3, 3), 0)

        enhanced = filtered
        if apply_clahe:
            # Contrast Limited Adaptive Histogram Equalization
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(filtered)

        return {
            "gray": gray,
            "bgr": bgr,
            "enhanced": enhanced,
            "skew_angle": skew_angle,
            "shape": gray.shape,
        }

    @staticmethod
    def deskew_image(
        gray: np.ndarray,
        bgr: Optional[np.ndarray] = None,
        max_angle: float = 35.0,
    ) -> Tuple[np.ndarray, Optional[np.ndarray], float]:
        """
        Detect skew angle from text blocks and rotate to horizontal.
        Only corrects skew within [-max_angle, max_angle] to avoid flipping.
        """
        # Invert colors so text is foreground
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # Find all white pixels (text/lines)
        coords = np.column_stack(np.where(thresh > 0))
        if len(coords) < 100:
            return gray, bgr, 0.0

        # Compute minimum area bounding box
        rect = cv2.minAreaRect(coords)
        angle = rect[-1]

        # OpenCV minAreaRect convention adjustments
        if angle < -45:
            angle = -(90 + angle)
        elif angle > 45:
            angle = 90 - angle

        # Ignore tiny or extreme angles
        if abs(angle) < 0.5 or abs(angle) > max_angle:
            return gray, bgr, 0.0

        (h, w) = gray.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated_gray = cv2.warpAffine(
            gray,
            M,
            (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE,
        )

        rotated_bgr = None
        if bgr is not None:
            rotated_bgr = cv2.warpAffine(
                bgr,
                M,
                (w, h),
                flags=cv2.INTER_CUBIC,
                borderMode=cv2.BORDER_REPLICATE,
            )

        logger.debug("Deskewed document by %.2f degrees", angle)
        return rotated_gray, rotated_bgr, float(angle)


# Singleton instance
_image_preprocessing_service: Optional[ImagePreprocessingService] = None


def get_image_preprocessing_service() -> ImagePreprocessingService:
    """Return shared ImagePreprocessingService singleton."""
    global _image_preprocessing_service
    if _image_preprocessing_service is None:
        _image_preprocessing_service = ImagePreprocessingService()
    return _image_preprocessing_service

