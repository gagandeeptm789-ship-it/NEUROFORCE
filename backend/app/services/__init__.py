"""
Services Package
"""

from app.services.auth_service import (
    authenticate_admin,
    ensure_default_admin,
    get_admin_by_email,
    get_admin_by_id,
    get_current_active_admin,
    get_current_admin,
    register_admin,
)
from app.services.crypto_service import (
    CryptoService,
    ICryptoService,
    Phase3PreparedCryptoService,
    get_crypto_service,
)
from app.services.hash_service import HashService
from app.services.signature_service import (
    SignatureService,
    get_signature_service,
)
from app.services.qr_service import (
    QRService,
    get_qr_service,
)
from app.services.watermark_service import (
    WatermarkService,
    get_watermark_service,
)
from app.services.pdf_publishing_service import (
    PDFPublishingService,
    get_pdf_publishing_service,
)
from app.services.notice_service import (
    create_notice,
    get_notice_by_id,
    get_notice_by_notice_id,
    list_notices,
    publish_notice,
    revoke_notice,
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
    "ensure_default_admin",
    "get_admin_by_email",
    "get_admin_by_id",
    "get_current_admin",
    "get_current_active_admin",
    "register_admin",
    "StorageService",
    "LocalStorageService",
    "SupabaseStorageService",
    "get_storage_service",
    "CryptoService",
    "ICryptoService",
    "Phase3PreparedCryptoService",
    "get_crypto_service",
    "HashService",
    "SignatureService",
    "get_signature_service",
    "QRService",
    "get_qr_service",
    "WatermarkService",
    "get_watermark_service",
    "PDFPublishingService",
    "get_pdf_publishing_service",
    "create_notice",
    "get_notice_by_id",
    "get_notice_by_notice_id",
    "list_notices",
    "publish_notice",
    "revoke_notice",
    "update_notice_status",
]
