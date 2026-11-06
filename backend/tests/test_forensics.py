"""
Image Forensics Engine Tests (Phase 6)
Verifies image preprocessing, geometric alignment, SSIM calculation,
and localized tampering detection vs uniform compression artifacts.
"""

import io
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import pytest

from app.services.image_preprocessing import ImagePreprocessingService, get_image_preprocessing_service
from app.services.image_matching import ImageMatchingService, get_image_matching_service
from app.services.tampering_detection import TamperingDetectionService, get_tampering_detection_service


def _create_sample_notice_image(title: str = "ANNUAL EXAMINATION SCHEDULE 2026", date_text: str = "DATE: 2026-04-15") -> Image.Image:
    """Helper to generate a clean synthetic university notice image."""
    width, height = 800, 1000
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # University Header
    draw.rectangle([30, 30, width - 30, 110], fill=(240, 245, 255), outline=(15, 23, 42), width=3)
    draw.text((50, 45), "GLOBAL METROPOLITAN UNIVERSITY", fill=(15, 23, 42))
    draw.text((50, 75), "OFFICE OF THE REGISTRAR & ACADEMIC EVALUATION", fill=(71, 85, 105))

    # Notice Title & Content
    draw.text((50, 150), title, fill=(15, 23, 42))
    draw.text((50, 200), date_text, fill=(30, 41, 59))
    draw.text((50, 240), "VENUE: Main Campus Convocation Auditorium Hall A", fill=(30, 41, 59))
    draw.text((50, 280), "All eligible candidates must present their verified university credentials.", fill=(30, 41, 59))
    draw.text((50, 320), "Admit cards must be signed by the Dean of Academic Affairs.", fill=(30, 41, 59))

    # Footer
    draw.rectangle([30, height - 90, width - 30, height - 30], fill=(248, 250, 252), outline=(15, 23, 42), width=1)
    draw.text((50, height - 70), "AUTHORIZED BY: Dr. Jane Doe (Controller of Examinations)", fill=(15, 23, 42))

    return img


def test_image_preprocessing_loading():
    """Verify document image loading from PIL, raw bytes, and numpy array."""
    prep = get_image_preprocessing_service()

    pil_img = _create_sample_notice_image()
    bgr, _ = prep.load_document_image(pil_img)

    assert bgr is not None
    assert bgr.shape[0] == 1000
    assert bgr.shape[1] == 800
    assert len(bgr.shape) == 3

    # From PNG bytes
    buf = io.BytesIO()
    pil_img.save(buf, format="PNG")
    bytes_data = buf.getvalue()

    bgr_from_bytes, _ = prep.load_document_image(bytes_data)
    assert bgr_from_bytes.shape == bgr.shape


def test_image_preprocessing_pipeline():
    """Verify grayscale, CLAHE, and noise filtering pipeline."""
    prep = get_image_preprocessing_service()
    pil_img = _create_sample_notice_image()
    bgr, _ = prep.load_document_image(pil_img)

    res = prep.preprocess_image(bgr, apply_deskew=False, apply_clahe=True, denoise=True)

    assert "gray" in res
    assert "enhanced" in res
    assert res["gray"].shape == (1000, 800)
    assert res["enhanced"].shape == (1000, 800)


def test_exact_image_ssim():
    """Verify SSIM calculation returns 1.0 for identical images."""
    matcher = get_image_matching_service()
    pil_img = _create_sample_notice_image()
    bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

    ssim_val, diff_map = matcher.compute_ssim(gray, gray)
    assert ssim_val >= 0.999
    assert np.max(diff_map) == 0


def test_transformed_image_detection():
    """Verify high-quality JPEG re-encoding maintains high SSIM without localized tampering."""
    tampering_svc = get_tampering_detection_service()
    prep = get_image_preprocessing_service()

    # Original
    orig_pil = _create_sample_notice_image()
    orig_bgr, _ = prep.load_document_image(orig_pil)

    # Simulate messaging compression (JPEG quality = 80)
    buf = io.BytesIO()
    orig_pil.save(buf, format="JPEG", quality=80)
    compressed_bytes = buf.getvalue()
    comp_bgr, _ = prep.load_document_image(compressed_bytes)

    report = tampering_svc.analyze_tampering(
        official_image=orig_bgr,
        uploaded_image=comp_bgr,
        notice_id="FS-GMU-2026-TEST01",
    )

    # Must classify as AUTHENTIC_TRANSFORMED with high score and no localized tampering
    assert report["status"] == "AUTHENTIC_TRANSFORMED"
    assert report["match_score"] >= 85
    assert len(report["suspicious_regions"]) == 0
    assert report["pixel_forensics"] == "JPEG_COMPRESSION_ARTIFACTS_ONLY"


def test_localized_tampering_detection():
    """Verify localized content modification (date alteration) is flagged with bounding box."""
    tampering_svc = get_tampering_detection_service()
    prep = get_image_preprocessing_service()

    # 1. Original document
    orig_pil = _create_sample_notice_image(date_text="DATE: 2026-04-15 (MANDATORY)")
    orig_bgr, _ = prep.load_document_image(orig_pil)

    # 2. Forged document: altered date and exam venue
    forged_pil = _create_sample_notice_image(date_text="DATE: 2026-07-28 (POSTPONED)")
    # Draw an explicit black alteration patch over the venue
    draw = ImageDraw.Draw(forged_pil)
    draw.rectangle([50, 240, 400, 260], fill=(255, 255, 255))
    draw.text((50, 240), "VENUE: CANCELLED UNTIL FURTHER NOTICE", fill=(200, 0, 0))

    forged_bgr, _ = prep.load_document_image(forged_pil)

    report = tampering_svc.analyze_tampering(
        official_image=orig_bgr,
        uploaded_image=forged_bgr,
        notice_id="FS-GMU-2026-TEST01",
    )

    assert report["status"] == "TAMPERING_DETECTED"
    assert report["match_score"] < 80
    assert len(report["suspicious_regions"]) >= 1
    assert any("Body Area" in reg["location"] or "Date" in reg["reason"] or reg["severity"] in ("HIGH", "MEDIUM") for reg in report["suspicious_regions"])
    assert report["annotated_preview"].startswith("data:image/")
    assert report["difference_preview"].startswith("data:image/")


def test_copied_qr_code_attack_detection():
    """Verify that a document bearing a copied QR code but completely mismatched content is flagged."""
    tampering_svc = get_tampering_detection_service()
    prep = get_image_preprocessing_service()

    # Official Exam Notice
    orig_pil = _create_sample_notice_image(title="FINAL EXAMINATION TIMETABLE")
    orig_bgr, _ = prep.load_document_image(orig_pil)

    # Completely different forged fee concession letter
    fake_img = Image.new("RGB", (800, 1000), color=(255, 255, 255))
    draw = ImageDraw.Draw(fake_img)
    draw.text((50, 50), "SPECIAL 100% TUITION FEE WAIVER AUTHORIZATION", fill=(0, 0, 0))
    draw.text((50, 100), "Payable balance: $0.00 immediately.", fill=(0, 0, 0))
    fake_bgr, _ = prep.load_document_image(fake_img)

    report = tampering_svc.analyze_tampering(
        official_image=orig_bgr,
        uploaded_image=fake_bgr,
        notice_id="FS-GMU-2026-OFFICIAL",
        qr_detected_id="FS-GMU-2026-OFFICIAL",  # Attacker pasted official QR onto fake letter
    )

    assert report["status"] == "TAMPERING_DETECTED"
    assert any("Copied QR Code Attack" in anomaly for anomaly in report["detected_anomalies"])

