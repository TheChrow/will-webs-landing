import enum
from datetime import datetime

from sqlalchemy import Boolean, Enum, ForeignKey, String, UniqueConstraint, false
from sqlalchemy.dialects.mysql import BINARY, MEDIUMTEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import PK, AuditMixin, CreatedAtMixin, IdMixin, Timestamp


class LegalDocumentType(enum.StrEnum):
    privacy = "privacy"
    cookies = "cookies"
    terms = "terms"
    accessibility = "accessibility"


class ConsentPurpose(enum.StrEnum):
    contact = "contact"
    marketing = "marketing"
    analytics_cookies = "analytics_cookies"


def _enum(e: type[enum.Enum], name: str) -> Enum:
    return Enum(e, name=name, values_callable=lambda x: [m.value for m in x], native_enum=True)


class LegalDocument(IdMixin, AuditMixin, Base):
    __tablename__ = "legal_document"

    type: Mapped[LegalDocumentType] = mapped_column(
        _enum(LegalDocumentType, "legal_document_type"), unique=True
    )
    slug: Mapped[str] = mapped_column(String(60), unique=True)
    title: Mapped[str] = mapped_column(String(160))

    versions: Mapped[list["LegalDocumentVersion"]] = relationship(back_populates="document")


class LegalDocumentVersion(IdMixin, AuditMixin, Base):
    __tablename__ = "legal_document_version"
    __table_args__ = (
        UniqueConstraint("document_id", "version", name="uq_legal_document_version_doc_version"),
    )

    document_id: Mapped[int] = mapped_column(
        PK, ForeignKey("legal_document.id", ondelete="RESTRICT")
    )
    version: Mapped[str] = mapped_column(String(20))
    body: Mapped[str] = mapped_column(MEDIUMTEXT)
    published_at: Mapped[datetime | None] = mapped_column(Timestamp)
    is_current: Mapped[bool] = mapped_column(Boolean, server_default=false(), default=False)

    document: Mapped[LegalDocument] = relationship(back_populates="versions")


class ConsentRecord(IdMixin, CreatedAtMixin, Base):
    """Append-only: una revocación es un nuevo registro con granted = False."""

    __tablename__ = "consent_record"

    legal_document_version_id: Mapped[int] = mapped_column(
        PK, ForeignKey("legal_document_version.id", ondelete="RESTRICT")
    )
    purpose: Mapped[ConsentPurpose] = mapped_column(_enum(ConsentPurpose, "consent_purpose"))
    granted: Mapped[bool] = mapped_column(Boolean)
    subject_email_hash: Mapped[bytes | None] = mapped_column(BINARY(32), index=True)
    ip_hash: Mapped[bytes | None] = mapped_column(BINARY(32))

    legal_document_version: Mapped[LegalDocumentVersion] = relationship()
