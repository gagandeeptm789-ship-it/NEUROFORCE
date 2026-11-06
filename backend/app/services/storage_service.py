"""
Storage Service Module
Provides an abstracted storage interface (StorageService) with LocalStorageService
and prepared SupabaseStorageService implementations.
Guarantees path traversal prevention and clean file lifecycle management.
"""

import abc
import os
import uuid
import logging
from typing import Optional

from app.core.config import get_settings
from app.utils.file_validator import sanitize_filename

logger = logging.getLogger("forwarded_seal.storage")
settings = get_settings()


class StorageService(abc.ABC):
    """Abstract file storage service."""

    @abc.abstractmethod
    def save_file(self, content: bytes, original_filename: str, subfolder: str = "") -> str:
        """Store bytes and return the canonical stored file path or identifier."""
        pass

    @abc.abstractmethod
    def get_file(self, stored_path: str) -> bytes:
        """Retrieve binary bytes of the stored file."""
        pass

    @abc.abstractmethod
    def delete_file(self, stored_path: str) -> bool:
        """Delete stored file if it exists."""
        pass

    @abc.abstractmethod
    def file_exists(self, stored_path: str) -> bool:
        """Check whether the stored file exists."""
        pass

    @abc.abstractmethod
    def get_absolute_path(self, stored_path: str) -> str:
        """Return absolute local filesystem path if available."""
        pass


class LocalStorageService(StorageService):
    """
    Local filesystem storage provider for development and standalone deployments.
    Enforces strict path containment within the configured upload root.
    """

    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = os.path.abspath(base_dir or settings.UPLOAD_DIR)
        os.makedirs(self.base_dir, exist_ok=True)
        logger.info("LocalStorageService initialized at root: %s", self.base_dir)

    def _resolve_safe_path(self, relative_path: str) -> str:
        """
        Resolve path and assert it is strictly within self.base_dir.
        Protects against Directory Traversal (CWE-22 / OWASP Top 10).
        """
        if relative_path is None:
            raise ValueError("Access denied: Empty storage path.")

        if os.path.isabs(relative_path):
            logger.error("Path traversal attempt detected: %s -> absolute path rejected", relative_path)
            raise ValueError("Access denied: Target path escapes upload root.")

        clean_rel = os.path.normpath(relative_path)
        if clean_rel in ("", "."):
            raise ValueError("Access denied: Empty storage path.")

        if clean_rel.startswith("..") or clean_rel.startswith("/") or clean_rel.startswith("\\"):
            logger.error("Path traversal attempt detected: %s -> %s", relative_path, clean_rel)
            raise ValueError("Access denied: Target path escapes upload root.")

        target_path = os.path.abspath(os.path.join(self.base_dir, clean_rel))

        # Boundary check
        common_prefix = os.path.commonpath([self.base_dir, target_path])
        if common_prefix != self.base_dir:
            logger.error("Path traversal attempt detected: %s -> %s", relative_path, target_path)
            raise ValueError("Access denied: Target path escapes upload root.")

        return target_path

    def save_file(self, content: bytes, original_filename: str, subfolder: str = "") -> str:
        """
        Save file to local disk with unique UUID prefix to prevent collisions.
        Returns a relative stored path suitable for database persistence.
        """
        clean_name = sanitize_filename(original_filename)
        _, ext = os.path.splitext(clean_name)
        file_uuid = uuid.uuid4().hex

        # Construct collision-free stored filename
        unique_filename = f"{file_uuid}_{clean_name}"
        relative_path = os.path.join(subfolder, unique_filename) if subfolder else unique_filename

        safe_full_path = self._resolve_safe_path(relative_path)
        os.makedirs(os.path.dirname(safe_full_path), exist_ok=True)

        with open(safe_full_path, "wb") as f:
            f.write(content)

        logger.info("Saved file (%d bytes) to %s", len(content), safe_full_path)
        # Store normalized path using forward slashes for cross-platform portability
        return relative_path.replace("\\", "/")

    def get_file(self, stored_path: str) -> bytes:
        """Read bytes from stored file."""
        safe_path = self._resolve_safe_path(stored_path)
        if not os.path.isfile(safe_path):
            raise FileNotFoundError(f"Stored file not found: {stored_path}")
        with open(safe_path, "rb") as f:
            return f.read()

    def delete_file(self, stored_path: str) -> bool:
        """Delete stored file from disk."""
        try:
            safe_path = self._resolve_safe_path(stored_path)
            if os.path.isfile(safe_path):
                os.remove(safe_path)
                logger.info("Deleted file %s", safe_path)
                return True
            return False
        except Exception as e:
            logger.error("Failed to delete file %s: %s", stored_path, e)
            return False

    def file_exists(self, stored_path: str) -> bool:
        """Check if file exists on disk."""
        try:
            safe_path = self._resolve_safe_path(stored_path)
            return os.path.isfile(safe_path)
        except ValueError:
            return False

    def get_absolute_path(self, stored_path: str) -> str:
        """Return absolute path for safe file streaming."""
        return self._resolve_safe_path(stored_path)


class SupabaseStorageService(StorageService):
    """
    Prepared Supabase Storage provider abstraction.
    Allows transparent migration to Supabase S3/Object Storage in Phase 3.
    """

    def __init__(self, supabase_url: str, supabase_key: str, bucket_name: str):
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.bucket_name = bucket_name
        logger.info("SupabaseStorageService ready for bucket '%s'", bucket_name)

    def save_file(self, content: bytes, original_filename: str, subfolder: str = "") -> str:
        clean_name = sanitize_filename(original_filename)
        object_key = f"{uuid.uuid4().hex}_{clean_name}"
        if subfolder:
            object_key = f"{subfolder.strip('/')}/{object_key}"
        # When Supabase client is configured in production, upload to bucket here
        logger.info("[SupabaseStorage] Mock uploaded object: %s", object_key)
        return object_key

    def get_file(self, stored_path: str) -> bytes:
        raise NotImplementedError("SupabaseStorageService.get_file requires active Supabase bucket credentials.")

    def delete_file(self, stored_path: str) -> bool:
        logger.info("[SupabaseStorage] Mock deleted object: %s", stored_path)
        return True

    def file_exists(self, stored_path: str) -> bool:
        return True

    def get_absolute_path(self, stored_path: str) -> str:
        raise NotImplementedError("Supabase objects are remote URLs, not local paths.")


def get_storage_service() -> StorageService:
    """Factory returning the active StorageService according to configuration."""
    provider = settings.STORAGE_PROVIDER.lower()
    if provider == "supabase" and settings.SUPABASE_URL and settings.SUPABASE_KEY:
        return SupabaseStorageService(
            supabase_url=settings.SUPABASE_URL,
            supabase_key=settings.SUPABASE_KEY,
            bucket_name=settings.SUPABASE_BUCKET_NAME,
        )
    return LocalStorageService()

