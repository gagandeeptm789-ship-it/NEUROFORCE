"""
Ed25519 Digital Signature System & Canonical Metadata Service
Implements asymmetric cryptographic signing and verification for college notices.
Provides secure local key storage, key ID management, key rotation, and revocation checks.
"""

import datetime
import json
import logging
import os
from typing import Any, Dict, Optional, Tuple

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

from app.core.config import get_settings

logger = logging.getLogger("forwarded_seal.signature")
settings = get_settings()

METADATA_VERSION = "1.0"
SIGNATURE_ALGORITHM = "Ed25519"
HASH_ALGORITHM = "SHA-256"


class SignatureService:
    """
    Manages Ed25519 asymmetric keys, canonical metadata formatting,
    digital signing, and signature verification.
    """

    def __init__(self, keys_dir: Optional[str] = None):
        # Resolve keys directory relative to backend root
        if keys_dir:
            self.keys_dir = keys_dir
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.keys_dir = os.path.join(base_dir, settings.KEYS_DIR)

        os.makedirs(self.keys_dir, exist_ok=True)
        self.registry_file = os.path.join(self.keys_dir, "key_registry.json")
        self._active_key_id: Optional[str] = None
        self._cached_private_keys: Dict[str, ed25519.Ed25519PrivateKey] = {}
        self._ensure_keys_initialized()

    # --------------------------------------------------------------------------
    # Key Store & Lifecycle Management
    # --------------------------------------------------------------------------

    def _load_registry(self) -> Dict[str, Any]:
        """Load the key registry from disk or return empty skeleton."""
        if os.path.exists(self.registry_file):
            try:
                with open(self.registry_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error("Failed to read key registry: %s", e)
        return {"active_key_id": None, "keys": {}}

    def _save_registry(self, registry: Dict[str, Any]) -> None:
        """Atomically persist key registry metadata."""
        temp_file = f"{self.registry_file}.tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(registry, f, indent=2, sort_keys=True)
        if os.path.exists(self.registry_file):
            os.replace(temp_file, self.registry_file)
        else:
            os.rename(temp_file, self.registry_file)

    def _ensure_keys_initialized(self) -> None:
        """
        Verify existing active key or generate the initial institutional signing key.
        Guarantees that a new key is NOT generated on every restart.
        """
        registry = self._load_registry()
        active_id = registry.get("active_key_id")

        if active_id and active_id in registry.get("keys", {}):
            key_meta = registry["keys"][active_id]
            priv_path = os.path.join(self.keys_dir, f"{active_id}.key")
            if os.path.exists(priv_path) and key_meta.get("status") == "active":
                self._active_key_id = active_id
                logger.info("Loaded active signing key: %s", active_id)
                return

        # No valid active key found: initialize default bootstrap key
        default_key_id = settings.SIGNING_KEY_ID or f"key-{settings.INSTITUTION_CODE}-2026-v1-ed25519"
        logger.info("Initializing initial institutional signing key: %s", default_key_id)
        self.generate_new_key(default_key_id, make_active=True)

    def generate_new_key(
        self,
        key_id: Optional[str] = None,
        make_active: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate a new Ed25519 keypair and register its public metadata.
        """
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()

        # Serialize public key
        pub_raw = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        pub_hex = pub_raw.hex()
        pub_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("utf-8")

        if not key_id:
            timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d%H%M%S")
            key_id = f"key-{settings.INSTITUTION_CODE}-{timestamp}-{pub_hex[:8]}"

        # Save private key securely to local key store
        priv_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        priv_path = os.path.join(self.keys_dir, f"{key_id}.key")
        with open(priv_path, "wb") as f:
            f.write(priv_bytes)

        # Restrict permissions where supported
        try:
            os.chmod(priv_path, 0o600)
        except Exception:
            pass

        key_info = {
            "key_id": key_id,
            "algorithm": SIGNATURE_ALGORITHM,
            "public_key_hex": pub_hex,
            "public_key_pem": pub_pem,
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "status": "active",
            "revoked_at": None,
        }

        registry = self._load_registry()
        registry["keys"][key_id] = key_info
        if make_active:
            registry["active_key_id"] = key_id
            self._active_key_id = key_id
        self._save_registry(registry)

        self._cached_private_keys[key_id] = private_key
        logger.info("Generated and registered Ed25519 key '%s' (active=%s)", key_id, make_active)
        return key_info

    def get_private_key(self, key_id: Optional[str] = None) -> ed25519.Ed25519PrivateKey:
        """Retrieve private key object from memory or disk for authorized signing."""
        target_id = key_id or self._active_key_id
        if not target_id:
            raise ValueError("No active signing key configured.")

        if target_id in self._cached_private_keys:
            return self._cached_private_keys[target_id]

        priv_path = os.path.join(self.keys_dir, f"{target_id}.key")
        if not os.path.exists(priv_path):
            raise FileNotFoundError(f"Private key file not found for key ID: {target_id}")

        with open(priv_path, "rb") as f:
            private_key = serialization.load_pem_private_key(f.read(), password=None)
            if not isinstance(private_key, ed25519.Ed25519PrivateKey):
                raise TypeError(f"Key {target_id} is not an Ed25519 private key.")

        self._cached_private_keys[target_id] = private_key
        return private_key

    def get_public_key_info(self, key_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieve trusted public key information by Key ID."""
        target_id = key_id or self._active_key_id
        registry = self._load_registry()
        return registry.get("keys", {}).get(target_id)

    def get_active_public_key_info(self) -> Optional[Dict[str, Any]]:
        """Retrieve the currently active public key information."""
        return self.get_public_key_info(self._active_key_id)

    def list_public_keys(self) -> Dict[str, Any]:
        """Return all trusted public keys in registry."""
        registry = self._load_registry()
        return {
            "active_key_id": registry.get("active_key_id"),
            "keys": registry.get("keys", {}),
        }

    def rotate_key(self, new_key_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Rotate institutional signing key.
        Creates a new active signing key. The prior key remains valid for signature verification.
        """
        logger.info("Rotating active signing key. Current active: %s", self._active_key_id)
        new_key = self.generate_new_key(key_id=new_key_id, make_active=True)
        return new_key

    def revoke_key(self, key_id: str) -> bool:
        """Mark a compromised or decommissioned key as revoked."""
        registry = self._load_registry()
        if key_id not in registry.get("keys", {}):
            return False

        registry["keys"][key_id]["status"] = "revoked"
        registry["keys"][key_id]["revoked_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

        if registry.get("active_key_id") == key_id:
            # Active key was revoked; generate fresh key to restore signing capability
            registry["active_key_id"] = None
            self._active_key_id = None
            self._save_registry(registry)
            self.generate_new_key(make_active=True)
        else:
            self._save_registry(registry)

        logger.warning("Revoked signing key: %s", key_id)
        return True

    # --------------------------------------------------------------------------
    # Canonical Metadata Formatting & Serialization
    # --------------------------------------------------------------------------

    @classmethod
    def create_canonical_metadata(
        cls,
        notice_id: str,
        title: str,
        description: Optional[str],
        category: str,
        issuer_name: str,
        issuer_id: str,
        created_at_iso: str,
        sha256_hash: str,
        signing_key_id: str,
        metadata_version: str = METADATA_VERSION,
    ) -> Dict[str, Any]:
        """
        Build the canonical deterministic dictionary to be signed.
        Guarantees exact field names, types, and omission of mutable dashboard stats.
        """
        return {
            "category": str(category).strip(),
            "created_at": str(created_at_iso).strip(),
            "description": str(description).strip() if description else "",
            "hash_algorithm": HASH_ALGORITHM,
            "issuer_id": str(issuer_id).strip(),
            "issuer_name": str(issuer_name).strip(),
            "metadata_version": str(metadata_version).strip(),
            "notice_id": str(notice_id).strip(),
            "sha256_hash": str(sha256_hash).strip().lower(),
            "signature_algorithm": SIGNATURE_ALGORITHM,
            "signing_key_id": str(signing_key_id).strip(),
            "title": str(title).strip(),
        }

    @classmethod
    def serialize_canonical_metadata(cls, metadata: Dict[str, Any]) -> bytes:
        """
        Deterministic JSON serialization:
        - Sorted keys
        - Compact separators (',', ':')
        - UTF-8 encoded bytes
        Ensures identical byte sequences across different platforms and runs.
        """
        return json.dumps(
            metadata,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8")

    # --------------------------------------------------------------------------
    # Digital Signing & Signature Verification
    # --------------------------------------------------------------------------

    def sign_metadata(
        self,
        metadata: Dict[str, Any],
        key_id: Optional[str] = None,
    ) -> Tuple[str, str]:
        """
        Sign canonical metadata using Ed25519 private key.
        Returns:
            (digital_signature_hex, signing_key_id)
        """
        target_key_id = key_id or self._active_key_id
        private_key = self.get_private_key(target_key_id)
        canonical_bytes = self.serialize_canonical_metadata(metadata)

        raw_signature = private_key.sign(canonical_bytes)
        signature_hex = raw_signature.hex()

        logger.debug(
            "Digitally signed notice %s with key %s (sig len: %d)",
            metadata.get("notice_id"),
            target_key_id,
            len(signature_hex),
        )
        return signature_hex, target_key_id

    def verify_signature(
        self,
        metadata: Dict[str, Any],
        signature_hex: str,
        key_id: str,
    ) -> Tuple[str, Optional[str]]:
        """
        Verify Ed25519 digital signature against canonical metadata and trusted public key.

        Returns:
            (status_code, reason_message)
            Status codes:
                - VALID_SIGNATURE
                - INVALID_SIGNATURE
                - UNKNOWN_KEY
                - REVOKED_KEY
                - INVALID_METADATA
        """
        if not metadata or not isinstance(metadata, dict):
            return "INVALID_METADATA", "Metadata is empty or malformed."

        if not signature_hex or not key_id:
            return "INVALID_METADATA", "Missing digital signature or signing key identifier."

        # 1. Retrieve public key metadata from registry
        key_info = self.get_public_key_info(key_id)
        if not key_info:
            return "UNKNOWN_KEY", f"Signing key '{key_id}' is not in the institutional trust registry."

        # 2. Check revocation status
        if key_info.get("status") == "revoked":
            return "REVOKED_KEY", f"Signing key '{key_id}' has been revoked (revoked at {key_info.get('revoked_at')})."

        # 3. Parse raw public key
        try:
            pub_bytes = bytes.fromhex(key_info["public_key_hex"])
            public_key = ed25519.Ed25519PublicKey.from_public_bytes(pub_bytes)
        except Exception as e:
            return "UNKNOWN_KEY", f"Failed to parse public key bytes: {e}"

        # 4. Parse signature bytes
        try:
            sig_bytes = bytes.fromhex(signature_hex.strip())
        except Exception:
            return "INVALID_SIGNATURE", "Signature is not valid hexadecimal format."

        # 5. Deterministically reconstruct canonical bytes
        try:
            canonical_bytes = self.serialize_canonical_metadata(metadata)
        except Exception as e:
            return "INVALID_METADATA", f"Failed to serialize canonical metadata: {e}"

        # 6. Verify signature
        try:
            public_key.verify(sig_bytes, canonical_bytes)
            return "VALID_SIGNATURE", "Ed25519 signature is authentic and verified."
        except InvalidSignature:
            return "INVALID_SIGNATURE", "Signature verification failed: payload or signature has been tampered with."
        except Exception as e:
            return "INVALID_SIGNATURE", f"Verification failed with error: {e}"


# Singleton helper
_signature_service_instance: Optional[SignatureService] = None


def get_signature_service() -> SignatureService:
    """Return shared SignatureService singleton."""
    global _signature_service_instance
    if _signature_service_instance is None:
        _signature_service_instance = SignatureService()
    return _signature_service_instance

