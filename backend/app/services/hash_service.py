"""
SHA-256 Hashing Service
Calculates deterministic cryptographic SHA-256 digests from files and raw bytes.
Uses chunked streaming to safely support large documents without excessive memory usage.
"""

import hashlib
import hmac
import os
from typing import BinaryIO, Dict, Union

DEFAULT_CHUNK_SIZE = 65536  # 64 KB streaming chunks


class HashService:
    """Service for computing and verifying SHA-256 cryptographic digests."""

    ALGORITHM: str = "SHA-256"

    @classmethod
    def calculate_bytes_hash(cls, data: bytes) -> Dict[str, str]:
        """
        Compute the SHA-256 checksum of raw in-memory bytes.
        Returns a dictionary with algorithm and 64-character lowercase hexadecimal digest.
        """
        hasher = hashlib.sha256()
        hasher.update(data)
        digest = hasher.hexdigest().lower()
        return {
            "algorithm": cls.ALGORITHM,
            "hash": digest,
        }

    @classmethod
    def calculate_file_hash(
        cls,
        file_input: Union[str, os.PathLike, BinaryIO],
        chunk_size: int = DEFAULT_CHUNK_SIZE,
    ) -> Dict[str, str]:
        """
        Compute SHA-256 digest from a file path or an open binary stream using chunked processing.
        Never alters or writes to the original file.
        """
        hasher = hashlib.sha256()

        if isinstance(file_input, (str, os.PathLike)):
            if not os.path.exists(file_input):
                raise FileNotFoundError(f"File not found for hashing: {file_input}")
            with open(file_input, "rb") as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    hasher.update(chunk)
        else:
            # Assume file-like object
            current_pos = None
            if hasattr(file_input, "tell") and hasattr(file_input, "seek"):
                try:
                    current_pos = file_input.tell()
                    file_input.seek(0)
                except Exception:
                    pass

            while True:
                chunk = file_input.read(chunk_size)
                if not chunk:
                    break
                hasher.update(chunk)

            # Reset pointer if it was seekable
            if current_pos is not None and hasattr(file_input, "seek"):
                try:
                    file_input.seek(current_pos)
                except Exception:
                    pass

        digest = hasher.hexdigest().lower()
        return {
            "algorithm": cls.ALGORITHM,
            "hash": digest,
        }

    @classmethod
    def compare_hashes(cls, hash1: str, hash2: str) -> bool:
        """
        Perform constant-time comparison between two hex digests to prevent timing attacks.
        """
        if not hash1 or not hash2:
            return False
        return hmac.compare_digest(hash1.strip().lower(), hash2.strip().lower())

    @classmethod
    def verify_file_integrity(
        cls,
        file_input: Union[str, os.PathLike, bytes],
        expected_hash: str,
    ) -> bool:
        """
        Verify if a given file or bytes match the expected SHA-256 hash.
        """
        if isinstance(file_input, bytes):
            result = cls.calculate_bytes_hash(file_input)
        else:
            result = cls.calculate_file_hash(file_input)

        return cls.compare_hashes(result["hash"], expected_hash)

