"""Registro de todos los modelos (Alembic autogenerate importa este paquete)."""

from app.models.auth import AdminUser, AuditLog, RefreshToken, Role, admin_user_role
from app.models.content import (
    Banner,
    ClientCompany,
    ContentBlock,
    Service,
    ServiceCategory,
    SiteSetting,
)
from app.models.leads import ContactMessage, ContactStatus
from app.models.legal import (
    ConsentPurpose,
    ConsentRecord,
    LegalDocument,
    LegalDocumentType,
    LegalDocumentVersion,
)

__all__ = [
    "AdminUser",
    "AuditLog",
    "Banner",
    "ClientCompany",
    "ConsentPurpose",
    "ConsentRecord",
    "ContactMessage",
    "ContactStatus",
    "ContentBlock",
    "LegalDocument",
    "LegalDocumentType",
    "LegalDocumentVersion",
    "RefreshToken",
    "Role",
    "Service",
    "ServiceCategory",
    "SiteSetting",
    "admin_user_role",
]
