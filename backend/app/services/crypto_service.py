"""
Cryptographic Service Interface (Phase 3 Preparation)
Defines contracts for SHA-256 document hashing, digital signing, and signature verification.
Keeps all cryptographic logic separated from API route handlers and database persistence.
"""

import abc
import hashlib
import json
import logging
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger("forwarded_seal.crypto")


class ICryptoService(abc.ABC):
    """Abstract interface for document hashing and digital signatures."""

    @abc.abstractmethod
    def calculate_sha256(self, data: bytes) -> str:
        """Calculate the hex-encoded SHA-256 checksum of raw binary data."""
        pass

    @abc.abstractmethod
    def generate_signed_metadata(
        self,
        notice_id: str,
        file_sha256: str,
        issuer_id: str,
        timestamp_iso: str,
    ) -> Dict[str, Any]:
        """Format the canonical metadata payload to be signed."""
        pass

    @abc.abstractmethod
    def sign_payload(self, payload: Dict[str, Any], key_id: Optional[str] = None) -> Tuple[str, str]:
        """Sign metadata using private key. Returns (signature_hex_or_b64, key_id)."""
        pass

    @abc.abstractmethod
    def verify_signature(
        self,
        payload: Dict[str, Any],
        signature: str,
        key_id: str,
    ) -> bool:
        """Verify the signature against the payload using the specified public key."""
        pass


class Phase3PreparedCryptoService(ICryptoService):
    """
    Preliminary cryptographic service for Phase 2.
    Provides standard SHA-256 hashing utility, and stubs ready for Phase 3
    asymmetric key signing (e.g. RSA-PSS or Ed25519).
    """

    def calculate_sha256(self, data: bytes) -> str:
        """
        Compute SHA-256 hash of document binary contents.
        Returns lowercase 64-character hexadecimal digest.
        """
        hasher = hashlib.sha256()
        hasher.update(data)
        digest = hasher.hexdigest()
        logger.debug("Computed SHA-256 digest: %s", digest)
        return digest

    def generate_signed_metadata(
        self,
        notice_id: str,
        file_sha256: str,
        issuer_id: str,
        timestamp_iso: str,
    ) -> Dict[str, Any]:
        """Standard canonical structure for notice signing in Phase 3."""
        return {
            "version": "1.0",
            "notice_id": notice_id,
            "document_sha256": file_sha256,
            "issuer_id": issuer_id,
            "timestamp": timestamp_iso,
        }

    def sign_payload(self, payload: Dict[str, Any], key_id: Optional[str] = None) -> Tuple[str, str]:
        """
        Stub for Phase 3 implementation.
        Phase 3 developer will wire private key infrastructure here.
        """
        logger.info("Phase 3 hook: sign_payload requested for %s", payload.get("notice_id"))
        return "PHASE_3_STUB_SIGNATURE", key_id or "key-phase3-dev-01"

    def verify_signature(
        self,
        payload: Dict[str, Any],
        signature: str,
        key_id: str,
    ) -> bool:
        """Stub for Phase 3 implementation."""
        logger.info("Phase 3 hook: verify_signature requested for key %s", key_id)
        return True


def get_crypto_service() -> ICryptoService:
    """Return configured crypto service instance."""
    return Phase3PreparedCryptoService()
