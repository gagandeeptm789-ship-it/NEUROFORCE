"""
Robust Digital Watermarking Service (DCT-Based Frequency Domain)
Implements mathematical frequency-domain 2D-DCT block watermarking on the luminance (Y) channel.
Embeds and extracts compact verification references with repetition coding and checksum integrity.
Resilient against moderate lossy JPEG re-compression, scaling, and messaging forward artifacts.
"""

import logging
import os
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
from PIL import Image
import scipy.fftpack

from app.core.config import get_settings

logger = logging.getLogger("forwarded_seal.watermark")
settings = get_settings()

PREAMBLE_SYNC_BYTE = 0xAB  # 10101011 synchronization marker
WATERMARK_FORMAT_VERSION = 1
BLOCK_SIZE = 8
# Mid-frequency coefficient pair inside 8x8 DCT matrix
COEFF_U1, COEFF_V1 = 3, 4
COEFF_U2, COEFF_V2 = 4, 3
DEFAULT_STRENGTH = 25.0  # Delta modulation amplitude for robust survival


def _bytes_to_bits(data: bytes) -> List[int]:
    """Convert bytes sequence into a list of 0/1 bits."""
    bits = []
    for byte in data:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
    return bits


def _bits_to_bytes(bits: List[int]) -> bytes:
    """Convert a list of 0/1 bits into bytes."""
    byte_list = []
    for i in range(0, len(bits), 8):
        byte_bits = bits[i : i + 8]
        if len(byte_bits) < 8:
            break
        val = 0
        for b in byte_bits:
            val = (val << 1) | b
        byte_list.append(val)
    return bytes(byte_list)


def _compute_checksum(data: bytes) -> int:
    """Calculate 8-bit XOR checksum with rotation."""
    chk = 0
    for b in data:
        chk = ((chk << 1) | (chk >> 7)) & 0xFF
        chk ^= b
    return chk


class WatermarkService:
    """
    DCT-based digital watermarking service for PNG and JPEG notices.
    """

    def __init__(self, watermark_dir: Optional[str] = None):
        if watermark_dir:
            self.watermark_dir = watermark_dir
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.watermark_dir = os.path.join(base_dir, settings.WATERMARK_DIR)

        os.makedirs(self.watermark_dir, exist_ok=True)

    def _prepare_payload_bits(self, notice_id: str) -> List[int]:
        """
        Encode Notice ID into a framed bitstream with preamble, version, length, and checksum.
        Format: [SYNC (1B)] [VERSION (1B)] [LEN (1B)] [NOTICE_ID (N B)] [CHECKSUM (1B)]
        """
        clean_id = notice_id.strip().encode("utf-8")
        if len(clean_id) > 60:
            clean_id = clean_id[:60]

        header_and_body = bytes([WATERMARK_FORMAT_VERSION, len(clean_id)]) + clean_id
        checksum = _compute_checksum(header_and_body)

        framed_packet = bytes([PREAMBLE_SYNC_BYTE]) + header_and_body + bytes([checksum])
        return _bytes_to_bits(framed_packet)

    def embed_watermark(
        self,
        input_image_path: str,
        notice_id: str,
        output_image_path: Optional[str] = None,
        strength: float = DEFAULT_STRENGTH,
    ) -> Tuple[str, str]:
        """
        Embed the notice reference into the frequency coefficients of the image.

        Returns:
            (saved_watermarked_path, watermark_reference)
        """
        if not os.path.exists(input_image_path):
            raise FileNotFoundError(f"Input image not found: {input_image_path}")

        # 1. Load image and convert to YCbCr
        img = Image.open(input_image_path)
        orig_mode = img.mode
        has_alpha = orig_mode == "RGBA"
        alpha_channel = None
        if has_alpha:
            alpha_channel = img.split()[-1]

        ycbcr = img.convert("YCbCr")
        y, cb, cr = ycbcr.split()
        y_arr = np.array(y, dtype=np.float32)

        height, width = y_arr.shape
        num_blocks_y = height // BLOCK_SIZE
        num_blocks_x = width // BLOCK_SIZE
        total_blocks = num_blocks_y * num_blocks_x

        payload_bits = self._prepare_payload_bits(notice_id)
        num_bits = len(payload_bits)

        if total_blocks < num_bits:
            raise ValueError(
                f"Image resolution too small for robust watermark embedding: "
                f"{width}x{height} yields {total_blocks} 8x8 blocks, requires {num_bits}."
            )

        # Repetition factor for spread spectrum redundancy
        repetition = max(1, total_blocks // num_bits)

        # 2. Iterate through 8x8 blocks and embed bits into mid-frequency DCT
        block_idx = 0
        for by in range(num_blocks_y):
            for bx in range(num_blocks_x):
                bit_idx = block_idx // repetition
                if bit_idx >= num_bits:
                    break  # All bits embedded with full repetition

                target_bit = payload_bits[bit_idx]

                y1, y2 = by * BLOCK_SIZE, (by + 1) * BLOCK_SIZE
                x1, x2 = bx * BLOCK_SIZE, (bx + 1) * BLOCK_SIZE
                block = y_arr[y1:y2, x1:x2]

                # 2D-DCT
                dct = scipy.fftpack.dct(
                    scipy.fftpack.dct(block.T, norm="ortho").T,
                    norm="ortho",
                )

                # Modulate coefficient pair (COEFF_U1, COEFF_V1) and (COEFF_U2, COEFF_V2)
                c1 = dct[COEFF_U1, COEFF_V1]
                c2 = dct[COEFF_U2, COEFF_V2]

                if target_bit == 1:
                    # Enforce c1 - c2 >= strength
                    if (c1 - c2) < strength:
                        mid = (c1 + c2) / 2.0
                        dct[COEFF_U1, COEFF_V1] = mid + (strength / 2.0)
                        dct[COEFF_U2, COEFF_V2] = mid - (strength / 2.0)
                else:
                    # Enforce c2 - c1 >= strength
                    if (c2 - c1) < strength:
                        mid = (c1 + c2) / 2.0
                        dct[COEFF_U1, COEFF_V1] = mid - (strength / 2.0)
                        dct[COEFF_U2, COEFF_V2] = mid + (strength / 2.0)

                # 2D-IDCT back to spatial domain
                idct = scipy.fftpack.idct(
                    scipy.fftpack.idct(dct.T, norm="ortho").T,
                    norm="ortho",
                )
                y_arr[y1:y2, x1:x2] = np.clip(idct, 0.0, 255.0)

                block_idx += 1

        # 3. Reconstruct image
        y_mod = Image.fromarray(y_arr.astype(np.uint8), mode="L")
        watermarked_img = Image.merge("YCbCr", (y_mod, cb, cr)).convert("RGB")

        if has_alpha and alpha_channel is not None:
            watermarked_img.putalpha(alpha_channel)

        # 4. Save to destination
        ext = os.path.splitext(input_image_path)[1].lower()
        if ext not in (".png", ".jpg", ".jpeg"):
            ext = ".png"

        if not output_image_path:
            clean_id = notice_id.replace("/", "_").replace(":", "_")
            output_image_path = os.path.join(self.watermark_dir, f"{clean_id}_watermarked{ext}")

        if ext in (".jpg", ".jpeg"):
            watermarked_img.convert("RGB").save(output_image_path, "JPEG", quality=95)
        else:
            watermarked_img.save(output_image_path, "PNG")

        logger.info(
            "Embedded DCT watermark for '%s' in %s (%d blocks, rep=%d)",
            notice_id,
            output_image_path,
            total_blocks,
            repetition,
        )
        return output_image_path, notice_id

    def extract_watermark(
        self,
        image_input: Union[str, Image.Image],
    ) -> Dict[str, Any]:
        """
        Extract embedded watermark from an image by evaluating mid-frequency DCT parity.

        Returns:
            {
                "detected": bool,
                "notice_id": Optional[str],
                "confidence": float,
                "version": int,
                "method": "2D-DCT Mid-Frequency"
            }
        """
        try:
            if isinstance(image_input, (str, os.PathLike)):
                if not os.path.exists(image_input):
                    return {
                        "detected": False,
                        "notice_id": None,
                        "confidence": 0.0,
                        "error": "Image file not found",
                    }
                img = Image.open(image_input)
            else:
                img = image_input

            ycbcr = img.convert("YCbCr")
            y, _, _ = ycbcr.split()
            y_arr = np.array(y, dtype=np.float32)

            height, width = y_arr.shape
            num_blocks_y = height // BLOCK_SIZE
            num_blocks_x = width // BLOCK_SIZE
            total_blocks = num_blocks_y * num_blocks_x

            if total_blocks < 32:
                return {
                    "detected": False,
                    "notice_id": None,
                    "confidence": 0.0,
                    "error": "Image too small for watermark recovery",
                }

            # 1. Extract raw bit votes for each 8x8 block
            raw_votes = []
            for by in range(num_blocks_y):
                for bx in range(num_blocks_x):
                    y1, y2 = by * BLOCK_SIZE, (by + 1) * BLOCK_SIZE
                    x1, x2 = bx * BLOCK_SIZE, (bx + 1) * BLOCK_SIZE
                    block = y_arr[y1:y2, x1:x2]

                    dct = scipy.fftpack.dct(
                        scipy.fftpack.dct(block.T, norm="ortho").T,
                        norm="ortho",
                    )
                    c1 = dct[COEFF_U1, COEFF_V1]
                    c2 = dct[COEFF_U2, COEFF_V2]
                    raw_votes.append(1 if (c1 > c2) else 0)

            # 2. Try variable repetition factors to detect framing
            # A typical notice payload is 20-30 bytes (~160-240 bits)
            best_match: Optional[Dict[str, Any]] = None

            for estimated_bits in range(120, min(360, total_blocks), 8):
                repetition = max(1, total_blocks // estimated_bits)
                if repetition < 1:
                    continue

                # Accumulate majority votes
                voted_bits = []
                for b_idx in range(estimated_bits):
                    sub = raw_votes[b_idx * repetition : (b_idx + 1) * repetition]
                    if not sub:
                        break
                    ones = sum(sub)
                    zeros = len(sub) - ones
                    voted_bits.append(1 if ones >= zeros else 0)

                decoded_bytes = _bits_to_bytes(voted_bits)
                if not decoded_bytes:
                    continue

                # Search for sync preamble
                sync_idx = decoded_bytes.find(bytes([PREAMBLE_SYNC_BYTE]))
                if sync_idx != -1 and sync_idx + 4 < len(decoded_bytes):
                    packet = decoded_bytes[sync_idx:]
                    ver = packet[1]
                    plen = packet[2]

                    if 4 <= plen <= 50 and (3 + plen + 1) <= len(packet):
                        payload_data = packet[3 : 3 + plen]
                        expected_chk = packet[3 + plen]

                        header_and_body = bytes([ver, plen]) + payload_data
                        calc_chk = _compute_checksum(header_and_body)

                        if calc_chk == expected_chk:
                            try:
                                notice_id_candidate = payload_data.decode("utf-8")
                                return {
                                    "detected": True,
                                    "notice_id": notice_id_candidate,
                                    "confidence": 1.0,
                                    "version": ver,
                                    "method": "2D-DCT Mid-Frequency Modulation",
                                }
                            except Exception:
                                pass

            # If framing checksum not fully verified, return no detection (real reporting per guidelines)
            return {
                "detected": False,
                "notice_id": None,
                "confidence": 0.0,
                "error": "Watermark unrecoverable or not present in image",
                "method": "2D-DCT Mid-Frequency Modulation",
            }
        except Exception as e:
            logger.error("Watermark extraction error: %s", e)
            return {
                "detected": False,
                "notice_id": None,
                "confidence": 0.0,
                "error": str(e),
                "method": "2D-DCT Mid-Frequency Modulation",
            }


# Singleton instance
_watermark_service_instance: Optional[WatermarkService] = None


def get_watermark_service() -> WatermarkService:
    """Return shared WatermarkService singleton."""
    global _watermark_service_instance
    if _watermark_service_instance is None:
        _watermark_service_instance = WatermarkService()
    return _watermark_service_instance

