"""
Cryptographic Service Interface & Integration
Unifies SHA-256 document hashing and Ed25519 digital signatures.
Extends ICryptoService interface with real cryptographic implementations.
"""

import logging
from typing import Any, Dict, Optional, Tuple

from app.services.hash_service import HashService
from app.services.signature_service import (
    SignatureService,
    get_signature_service,
    METADATA_VERSION,
    SIGNATURE_ALGORITHM,
    HASH_ALGORITHM,
)

logger = logging.getLogger("forwarded_seal.crypto")


class CryptoService:
    """Production cryptographic service for Phase 3 and Phase 4."""

    def __init__(self, signature_service: Optional[SignatureService] = None):
        self.signature_service = signature_service or get_signature_service()

    def calculate_sha256(self, data: bytes) -> str:
        """Compute SHA-256 hex digest from bytes."""
        return HashService.calculate_bytes_hash(data)["hash"]

    def calculate_file_sha256(self, file_path: str) -> str:
        """Compute SHA-256 hex digest from file using streaming chunks."""
        return HashService.calculate_file_hash(file_path)["hash"]

    def generate_signed_metadata(
        self,
        notice_id: str,
        file_sha256: str,
        issuer_id: str,
        title: str = "Official Notice",
        category: str = "General",
        issuer_name: str = "Administrator",
        created_at_iso: Optional[str] = None,
        timestamp_iso: Optional[str] = None,
        description: Optional[str] = None,
        signing_key_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Format canonical metadata payload with backward-compatible keyword arguments."""
        iso_time = created_at_iso or timestamp_iso or "2026-01-01T00:00:00Z"
        key_id = signing_key_id or self.signature_service._active_key_id or "default"
        meta = self.signature_service.create_canonical_metadata(
            notice_id=notice_id,
            title=title,
            description=description,
            category=category,
            issuer_name=issuer_name,
            issuer_id=issuer_id,
            created_at_iso=iso_time,
            sha256_hash=file_sha256,
            signing_key_id=key_id,
            metadata_version=METADATA_VERSION,
        )
        meta["version"] = meta.get("metadata_version", METADATA_VERSION)
        meta["document_sha256"] = meta.get("sha256_hash")
        meta["timestamp"] = meta.get("created_at")
        return meta

    def sign_payload(self, payload: Dict[str, Any], key_id: Optional[str] = None) -> Tuple[str, str]:
        """Sign metadata using Ed25519 private key. Returns (signature_hex, key_id)."""
        return self.signature_service.sign_metadata(payload, key_id=key_id)

    def verify_signature(
        self,
        payload: Dict[str, Any],
        signature_hex: str,
        key_id: str,
    ) -> Tuple[str, Optional[str]]:
        """Verify signature against canonical metadata and trusted public key."""
        return self.signature_service.verify_signature(payload, signature_hex, key_id)


# Backward compatibility aliases for Phase 2 contracts
ICryptoService = CryptoService
Phase3PreparedCryptoService = CryptoService


def get_crypto_service() -> CryptoService:
    """Return configured crypto service instance."""
    return CryptoService()
