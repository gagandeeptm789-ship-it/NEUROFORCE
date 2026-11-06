"""
Storage, Notice ID, and Cryptographic Compatibility Unit Tests
Verifies Notice ID uniqueness, path traversal protections, and Phase 3 SHA-256 hashing hooks.
"""

import hashlib
import os
import pytest
from app.services.crypto_service import Phase3PreparedCryptoService
from app.services.storage_service import LocalStorageService
from app.utils.file_validator import sanitize_filename
from app.utils.notice_id import generate_raw_notice_id


def test_notice_id_format_and_uniqueness():
    """Verify that generated Notice IDs follow the expected institutional format and are unique."""
    generated_ids = set()
    for _ in range(100):
        nid = generate_raw_notice_id(prefix="FS", institution="GMU", year=2026)
        assert nid.startswith("FS-GMU-2026-")
        parts = nid.split("-")
        assert len(parts) == 4
        assert len(parts[3]) == 6  # 6 hex chars
        assert nid not in generated_ids
        generated_ids.add(nid)

    assert len(generated_ids) == 100


def test_storage_path_traversal_protection(temp_storage_dir):
    """
    Verify that LocalStorageService rejects directory traversal attacks (CWE-22).
    Attempts to escape the base directory using ../ must raise a ValueError.
    """
    storage = LocalStorageService(base_dir=temp_storage_dir)

    malicious_paths = [
        "../../etc/passwd",
        "..\\..\\windows\\system32\\cmd.exe",
        "subfolder/../../../secret.txt",
    ]

    for bad_path in malicious_paths:
        with pytest.raises(ValueError, match="Target path escapes upload root"):
            storage.save_file(b"malicious data", "test.pdf", subfolder=bad_path)

        with pytest.raises(ValueError, match="Target path escapes upload root"):
            storage.get_file(bad_path)


def test_storage_lifecycle(temp_storage_dir):
    """Verify complete save, retrieve, check existence, and delete lifecycle."""
    storage = LocalStorageService(base_dir=temp_storage_dir)
    test_content = b"%PDF-1.4 sample document bytes"

    # Save
    stored_path = storage.save_file(test_content, "sample document.pdf", subfolder="notices")
    assert storage.file_exists(stored_path) is True

    # Retrieve
    retrieved_bytes = storage.get_file(stored_path)
    assert retrieved_bytes == test_content

    # Delete
    deleted = storage.delete_file(stored_path)
    assert deleted is True
    assert storage.file_exists(stored_path) is False


def test_sanitize_filename():
    """Verify filename sanitization strips directory slashes and unsafe characters."""
    assert sanitize_filename("../../../malicious file name.pdf") == "malicious_file_name.pdf"
    assert sanitize_filename("safe_name.png") == "safe_name.png"
    assert sanitize_filename("file;rm -rf.jpg") == "file_rm_-rf.jpg"


def test_crypto_service_sha256_calculation():
    """Verify Phase 3 preparation: SHA-256 calculation matches hashlib standard."""
    crypto = Phase3PreparedCryptoService()
    test_data = b"The Forwarded Seal Document Verification Payload 2026"
    expected_hash = hashlib.sha256(test_data).hexdigest()

    result_hash = crypto.calculate_sha256(test_data)
    assert result_hash == expected_hash
    assert len(result_hash) == 64


def test_crypto_service_metadata_formatting():
    """Verify that canonical signed metadata structure is properly formatted for Phase 3."""
    crypto = Phase3PreparedCryptoService()
    metadata = crypto.generate_signed_metadata(
        notice_id="FS-GMU-2026-A8F29C",
        file_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        issuer_id="admin-uuid-1234",
        timestamp_iso="2026-11-06T10:00:00Z",
    )
    assert metadata["version"] == "1.0"
    assert metadata["notice_id"] == "FS-GMU-2026-A8F29C"
    assert metadata["document_sha256"] == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    assert metadata["issuer_id"] == "admin-uuid-1234"
    assert metadata["timestamp"] == "2026-11-06T10:00:00Z"

