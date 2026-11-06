"""
Image Matching & Alignment Service
Performs ORB feature detection, homography estimation, perspective warping,
structural similarity index (SSIM) calculation, and difference mapping between
official registered notice documents and student-uploaded copies.
"""

import logging
from typing import Any, Dict, Optional, Tuple

import cv2
import numpy as np

from app.services.image_preprocessing import ImagePreprocessingService

logger = logging.getLogger("forwarded_seal.image_matching")


class ImageMatchingService:
    """Service for robust geometric alignment and structural comparison of document images."""

    def __init__(self, max_features: int = 3000, ratio_threshold: float = 0.75):
        self.max_features = max_features
        self.ratio_threshold = ratio_threshold
        self.orb = cv2.ORB_create(
            nfeatures=self.max_features,
            scaleFactor=1.2,
            nlevels=8,
            edgeThreshold=31,
            firstLevel=0,
            WTA_K=2,
            scoreType=cv2.ORB_HARRIS_SCORE,
            patchSize=31,
            fastThreshold=20,
        )
        self.bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)

    @staticmethod
    def compute_ssim(
        img1: np.ndarray,
        img2: np.ndarray,
    ) -> Tuple[float, np.ndarray]:
        """
        Compute the Structural Similarity Index (SSIM) between two single-channel (gray) images.
        Follows the standard formulation of Wang, Bovik, Sheikh, & Simoncelli (2004).

        Returns:
            Tuple of (mean_ssim_score, ssim_difference_map)
        """
        if img1.shape != img2.shape:
            raise ValueError(f"Images must have identical dimensions for SSIM: {img1.shape} vs {img2.shape}")

        C1 = (0.01 * 255) ** 2
        C2 = (0.03 * 255) ** 2

        img1_f = img1.astype(np.float64)
        img2_f = img2.astype(np.float64)

        # 11x11 Gaussian window with sigma = 1.5
        kernel_size = (11, 11)
        sigma = 1.5

        mu1 = cv2.GaussianBlur(img1_f, kernel_size, sigma)
        mu2 = cv2.GaussianBlur(img2_f, kernel_size, sigma)

        mu1_sq = mu1 ** 2
        mu2_sq = mu2 ** 2
        mu1_mu2 = mu1 * mu2

        sigma1_sq = cv2.GaussianBlur(img1_f ** 2, kernel_size, sigma) - mu1_sq
        sigma2_sq = cv2.GaussianBlur(img2_f ** 2, kernel_size, sigma) - mu2_sq
        sigma12 = cv2.GaussianBlur(img1_f * img2_f, kernel_size, sigma) - mu1_mu2

        numerator = (2.0 * mu1_mu2 + C1) * (2.0 * sigma12 + C2)
        denominator = (mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2)

        ssim_map = numerator / (denominator + 1e-10)
        mean_ssim = float(np.mean(ssim_map))

        # Clamp mean SSIM to [0.0, 1.0] for reporting
        clamped_score = max(0.0, min(1.0, mean_ssim))

        # Normalized structural difference map: higher values indicate greater dissimilarity
        diff_map = np.clip((1.0 - ssim_map) * 255.0, 0, 255).astype(np.uint8)

        return clamped_score, diff_map

    def align_and_compare(
        self,
        official_bgr: np.ndarray,
        uploaded_bgr: np.ndarray,
    ) -> Dict[str, Any]:
        """
        Geometrically align the uploaded document to match the official document's coordinates,
        then calculate SSIM, difference map, and feature matching metrics.
        """
        target_h, target_w = official_bgr.shape[:2]

        # 1. Preprocess both images
        prep = ImagePreprocessingService()
        official_prep = prep.preprocess_image(official_bgr, apply_deskew=False, apply_clahe=False)
        uploaded_prep = prep.preprocess_image(uploaded_bgr, apply_deskew=True, apply_clahe=False)

        official_gray = official_prep["gray"]
        uploaded_gray = uploaded_prep["gray"]
        uploaded_deskewed_bgr = uploaded_prep["bgr"]

        # 2. Extract ORB features
        kp1, des1 = self.orb.detectAndCompute(official_gray, None)
        kp2, des2 = self.orb.detectAndCompute(uploaded_gray, None)

        homography_used = False
        inlier_count = 0
        inlier_ratio = 0.0
        aligned_bgr = None

        if des1 is not None and des2 is not None and len(des1) >= 10 and len(des2) >= 10:
            try:
                # Match descriptors using k-NN with k=2 for ratio test
                matches = self.bf.knnMatch(des2, des1, k=2)
                good_matches = []
                for m_n in matches:
                    if len(m_n) == 2:
                        m, n = m_n
                        if m.distance < self.ratio_threshold * n.distance:
                            good_matches.append(m)

                if len(good_matches) >= 10:
                    src_pts = np.float32([kp2[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
                    dst_pts = np.float32([kp1[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)

                    H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)

                    if H is not None and mask is not None:
                        inliers = int(np.sum(mask))
                        inlier_ratio = inliers / float(len(good_matches))

                        # Verify homography validity (non-degenerate transformation)
                        det = np.linalg.det(H[:2, :2])
                        if det > 0.1 and det < 10.0 and inliers >= 8:
                            aligned_bgr = cv2.warpPerspective(
                                uploaded_deskewed_bgr,
                                H,
                                (target_w, target_h),
                                flags=cv2.INTER_CUBIC,
                                borderMode=cv2.BORDER_REPLICATE,
                            )
                            homography_used = True
                            inlier_count = inliers
            except Exception as e:
                logger.debug("Feature-based alignment encountered error, falling back to resize: %s", e)

        # 3. Fallback: Proportional direct resize if homography was not usable
        if aligned_bgr is None:
            aligned_bgr = cv2.resize(
                uploaded_deskewed_bgr,
                (target_w, target_h),
                interpolation=cv2.INTER_CUBIC,
            )

        # 4. Convert aligned image to grayscale for direct comparison
        aligned_gray = cv2.cvtColor(aligned_bgr, cv2.COLOR_BGR2GRAY)

        # 5. Compute SSIM and difference map
        ssim_score, ssim_diff_map = self.compute_ssim(official_gray, aligned_gray)

        # 6. Direct pixel difference
        abs_diff = cv2.absdiff(official_gray, aligned_gray)

        # Determine alignment quality descriptor
        if homography_used and inlier_count >= 30:
            alignment_quality = "EXCELLENT"
        elif homography_used and inlier_count >= 12:
            alignment_quality = "GOOD"
        elif inlier_count >= 6:
            alignment_quality = "MODERATE"
        else:
            alignment_quality = "DIRECT_SCALED"

        return {
            "official_gray": official_gray,
            "aligned_bgr": aligned_bgr,
            "aligned_gray": aligned_gray,
            "ssim_score": ssim_score,
            "ssim_diff_map": ssim_diff_map,
            "abs_diff": abs_diff,
            "homography_used": homography_used,
            "inlier_count": inlier_count,
            "inlier_ratio": inlier_ratio,
            "alignment_quality": alignment_quality,
        }


# Singleton instance
_image_matching_service: Optional[ImageMatchingService] = None


def get_image_matching_service() -> ImageMatchingService:
    """Return shared ImageMatchingService singleton."""
    global _image_matching_service
    if _image_matching_service is None:
        _image_matching_service = ImageMatchingService()
    return _image_matching_service

