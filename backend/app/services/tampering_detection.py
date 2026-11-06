"""
Tampering Detection & Image Forensics Engine
Detects localized pixel modifications, spliced text, modified dates, copied verification marks,
and distinguishes uniform compression/messaging artifacts from intentional document forgery.
"""

import base64
import io
import logging
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image

from app.services.image_matching import ImageMatchingService, get_image_matching_service
from app.services.image_preprocessing import ImagePreprocessingService, get_image_preprocessing_service

logger = logging.getLogger("forwarded_seal.tampering_detection")


class TamperingDetectionService:
    """Service for localized tampering detection, artifact discrimination, and forensic reporting."""

    def __init__(
        self,
        matching_service: Optional[ImageMatchingService] = None,
        preprocessing_service: Optional[ImagePreprocessingService] = None,
        min_contour_area: int = 120,
        tampering_ssim_threshold: float = 0.85,
    ):
        self.matching_service = matching_service or get_image_matching_service()
        self.preprocessing_service = preprocessing_service or get_image_preprocessing_service()
        self.min_contour_area = min_contour_area
        self.tampering_ssim_threshold = tampering_ssim_threshold

    @staticmethod
    def encode_cv2_image_to_data_uri(img_bgr: np.ndarray, format: str = ".jpg") -> str:
        """Encode an OpenCV image to a base64 Data URI."""
        encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), 85] if format in (".jpg", ".jpeg") else []
        success, buffer = cv2.imencode(format, img_bgr, encode_params)
        if not success:
            return ""
        b64 = base64.b64encode(buffer).decode("utf-8")
        mime = "image/jpeg" if format in (".jpg", ".jpeg") else "image/png"
        return f"data:{mime};base64,{b64}"

    def analyze_tampering(
        self,
        official_image: np.ndarray,
        uploaded_image: np.ndarray,
        notice_id: str,
        official_title: Optional[str] = None,
        official_category: Optional[str] = None,
        qr_detected_id: Optional[str] = None,
        watermark_detected_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Conduct deep forensic analysis comparing official document against student-uploaded document.

        Returns comprehensive forensic report containing:
        - `status`: "AUTHENTIC", "AUTHENTIC_TRANSFORMED", "TAMPERING_DETECTED", or "UNVERIFIABLE"
        - `match_score`: integer confidence score (0-100)
        - `pixel_forensics`: diagnostic string
        - `ssim_score`: float
        - `suspicious_regions`: list of bounding boxes with coordinates and severity
        - `detected_anomalies`: list of descriptive forensic alerts
        - `verdict_summary`: detailed human-readable explanation
        - `annotated_preview`: base64 image data URI showing highlighted suspicious areas
        - `difference_preview`: base64 image data URI showing structural difference map
        """
        # 1. Align uploaded document to official geometry and calculate SSIM & differences
        match_result = self.matching_service.align_and_compare(official_image, uploaded_image)

        official_gray = match_result["official_gray"]
        aligned_bgr = match_result["aligned_bgr"]
        aligned_gray = match_result["aligned_gray"]
        ssim_score = match_result["ssim_score"]
        abs_diff = match_result["abs_diff"]
        ssim_diff_map = match_result["ssim_diff_map"]

        height, width = official_gray.shape[:2]
        total_pixels = height * width

        # 2. Discriminate uniform compression from localized alterations
        # Calculate combined difference metric
        combined_diff = cv2.addWeighted(abs_diff, 0.6, ssim_diff_map, 0.4, 0)

        # Thresholding: isolate high-intensity differences
        _, thresh = cv2.threshold(combined_diff, 45, 255, cv2.THRESH_BINARY)

        # Morphological Closing: merge nearby altered character strokes/words into unified regions
        close_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
        closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, close_kernel)

        # Morphological Opening: eliminate isolated single-pixel JPEG/compression specks
        open_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        filtered_mask = cv2.morphologyEx(closed, cv2.MORPH_OPEN, open_kernel)

        # 3. Find contours of suspicious modified regions
        contours, _ = cv2.findContours(filtered_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        suspicious_regions: List[Dict[str, Any]] = []
        annotated_bgr = aligned_bgr.copy()

        total_tampered_area = 0

        for idx, cnt in enumerate(contours):
            area = cv2.contourArea(cnt)
            if area < self.min_contour_area:
                continue

            x, y, w, h = cv2.boundingRect(cnt)
            total_tampered_area += area

            # Mask out region to inspect internal variation
            region_mask = filtered_mask[y : y + h, x : x + w]
            density = float(np.sum(region_mask > 0)) / float(w * h)

            # Determine severity
            if area > 1200 or density > 0.4:
                severity = "HIGH"
                box_color = (0, 0, 255)  # Red BGR
            elif area > 400 or density > 0.25:
                severity = "MEDIUM"
                box_color = (0, 140, 255)  # Orange BGR
            else:
                severity = "LOW"
                box_color = (0, 220, 255)  # Yellow BGR

            # Draw glowing bounding box
            cv2.rectangle(annotated_bgr, (x, y), (x + w, y + h), box_color, 2)
            cv2.putText(
                annotated_bgr,
                f"SUSP-{idx+1} [{severity}]",
                (x, max(15, y - 6)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                box_color,
                1,
                cv2.LINE_AA,
            )

            # Document location classification
            rel_y = y / float(height)
            if rel_y < 0.22:
                loc_name = "Header / Letterhead Area"
            elif rel_y > 0.78:
                loc_name = "Footer / Signatory Area"
            else:
                loc_name = "Notice Content / Body Area"

            suspicious_regions.append({
                "region_id": f"SUSP-{idx+1}",
                "location": loc_name,
                "coordinates": {"x": int(x), "y": int(y), "w": int(w), "h": int(h)},
                "area_pixels": int(area),
                "severity": severity,
                "reason": f"Localized pixel modification ({severity} intensity) detected in {loc_name}.",
            })

        tampered_ratio = total_tampered_area / float(total_pixels)
        detected_anomalies: List[str] = []

        # 4. Check for Copied Verification Mark Attacks
        # If QR code or watermark claims notice_id X, but the visual content exhibits mismatch
        copied_mark_attack = False
        inlier_count = match_result.get("inlier_count", 0)

        if qr_detected_id and qr_detected_id.upper() == notice_id.upper():
            if inlier_count < 8 or ssim_score < 0.94 or len(suspicious_regions) > 0:
                copied_mark_attack = True
                detected_anomalies.append(
                    f"CRITICAL: Copied QR Code Attack Detected. An authentic QR watermark for notice "
                    f"'{notice_id}' was attached to an unauthorized or materially altered document."
                )

        if watermark_detected_id and watermark_detected_id.upper() == notice_id.upper():
            if inlier_count < 8 or ssim_score < 0.94 or len(suspicious_regions) > 0:
                copied_mark_attack = True
                detected_anomalies.append(
                    f"CRITICAL: Copied Steganographic Watermark Attack Detected. The hidden watermark "
                    f"for notice '{notice_id}' is present, but image structural integrity failed."
                )

        # 5. Formulate Forensic Status & Diagnostics
        if copied_mark_attack or len(suspicious_regions) > 0 or ssim_score < self.tampering_ssim_threshold:
            if copied_mark_attack:
                status = "TAMPERING_DETECTED"
                pixel_forensics = "CRITICAL_MARK_SPLICING_DETECTED"
                match_score = max(5, int(ssim_score * 40))
                verdict_summary = (
                    "CRITICAL FORGERY WARNING: This notice contains authentic institutional identification "
                    "marks that appear to have been copied or spliced onto an altered or fraudulent document. "
                    "Do not trust the forwarded contents."
                )
            else:
                status = "TAMPERING_DETECTED"
                pixel_forensics = "LOCALIZED_TAMPERING_DETECTED"
                match_score = max(15, min(65, int(ssim_score * 70)))
                detected_anomalies.append(
                    f"{len(suspicious_regions)} localized pixel alteration region(s) identified in document."
                )
                verdict_summary = (
                    f"Warning: Forensic inspection detected {len(suspicious_regions)} localized content "
                    f"modification(s) differing from the registered official circular. Key information such as "
                    f"dates, titles, or examination schedules may have been modified."
                )
        else:
            # Survived compression/resizing without localized alterations
            status = "AUTHENTIC_TRANSFORMED"
            pixel_forensics = "JPEG_COMPRESSION_ARTIFACTS_ONLY" if ssim_score < 0.999 else "CLEAN_NO_ALTERATION"
            match_score = max(88, min(98, int(ssim_score * 100)))
            detected_anomalies.append(
                "Global uniform compression noise detected consistent with social media / messaging forwarding."
            )
            verdict_summary = (
                "Authentic official notice verified. The document has undergone messaging compression or "
                "screenshot re-encoding, but official text and structural content remain unaltered."
            )

        # 6. Generate Difference Heatmap Preview
        diff_colored = cv2.applyColorMap(combined_diff, cv2.COLORMAP_JET)
        # Blend difference with original for intuitive visual representation
        blended_diff = cv2.addWeighted(official_image, 0.45, diff_colored, 0.55, 0)

        annotated_preview_uri = self.encode_cv2_image_to_data_uri(annotated_bgr, ".jpg")
        difference_preview_uri = self.encode_cv2_image_to_data_uri(blended_diff, ".jpg")

        return {
            "status": status,
            "match_score": match_score,
            "ssim_score": round(ssim_score, 4),
            "pixel_forensics": pixel_forensics,
            "tampered_ratio": round(tampered_ratio, 4),
            "suspicious_regions": suspicious_regions,
            "detected_anomalies": detected_anomalies,
            "verdict_summary": verdict_summary,
            "alignment_quality": match_result["alignment_quality"],
            "annotated_preview": annotated_preview_uri,
            "difference_preview": difference_preview_uri,
        }


# Singleton instance
_tampering_detection_service: Optional[TamperingDetectionService] = None


def get_tampering_detection_service() -> TamperingDetectionService:
    """Return shared TamperingDetectionService singleton."""
    global _tampering_detection_service
    if _tampering_detection_service is None:
        _tampering_detection_service = TamperingDetectionService()
    return _tampering_detection_service
