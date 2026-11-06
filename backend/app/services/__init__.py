"""
Services Package
"""

from app.services.auth_service import (
    authenticate_admin,
    get_admin_by_email,
    get_admin_by_id,
    get_current_active_admin,
    get_current_admin,
    register_admin,
)
from app.services.crypto_service import (
    ICryptoService,
    Phase3PreparedCryptoService,
    get_crypto_service,
)
from app.services.notice_service import (
    create_notice,
    get_notice_by_id,
    get_notice_by_notice_id,
    list_notices,
    prepare_phase3_signing_payload,
    update_notice_status,
)
from app.services.storage_service import (
    LocalStorageService,
    StorageService,
    SupabaseStorageService,
    get_storage_service,
)

__all__ = [
    "authenticate_admin",
    "get_admin_by_email",
    "get_admin_by_id",
    "get_current_admin",
    "get_current_active_admin",
    "register_admin",
    "StorageService",
    "LocalStorageService",
    "SupabaseStorageService",
    "get_storage_service",
    "ICryptoService",
    "Phase3PreparedCryptoService",
    "get_crypto_service",
    "create_notice",
    "get_notice_by_id",
    "get_notice_by_notice_id",
    "list_notices",
    "update_notice_status",
    "prepare_phase3_signing_payload",
]

