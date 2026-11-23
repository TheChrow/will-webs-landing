import enum
from datetime import date, datetime

from sqlalchemy import Date, Enum, ForeignKey, Index, String, Text
from sqlalchemy.dialects.mysql import BINARY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.content import Service
from app.models.legal import ConsentRecord
from app.models.mixins import PK, AuditMixin, IdMixin, PublicIdMixin, Timestamp


class ContactStatus(enum.StrEnum):
    new = "new"
    read = "read"
    contacted = "contacted"
    archived = "archived"
    spam = "spam"


class ContactMessage(IdMixin, PublicIdMixin, AuditMixin, Base):
    """Lead del formulario de contacto. Contiene DATOS PERSONALES (ver política de retención)."""

    __tablename__ = "contact_message"
    __table_args__ = (
        Index("ix_contact_message_status_created", "status", "created_at"),
        Index("ix_contact_message_email", "email"),
        Index("ix_contact_message_retention_until", "retention_until"),
    )

    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(254))
    company: Mapped[str | None] = mapped_column(String(160))
    phone: Mapped[str | None] = mapped_column(String(32))
    service_id: Mapped[int | None] = mapped_column(
        PK, ForeignKey("service.id", ondelete="SET NULL"), nullable=True
    )
    message: Mapped[str | None] = mapped_column(Text)  # NULL solo tras anonimizar
    status: Mapped[ContactStatus] = mapped_column(
        Enum(
            ContactStatus,
            name="contact_status",
            values_callable=lambda x: [m.value for m in x],
        ),
        server_default=ContactStatus.new.value,
        default=ContactStatus.new,
    )
    consent_record_id: Mapped[int] = mapped_column(
        PK, ForeignKey("consent_record.id", ondelete="RESTRICT")
    )
    ip_hash: Mapped[bytes | None] = mapped_column(BINARY(32))
    user_agent: Mapped[str | None] = mapped_column(String(255))
    retention_until: Mapped[date] = mapped_column(Date)
    anonymized_at: Mapped[datetime | None] = mapped_column(Timestamp)

    service: Mapped[Service | None] = relationship()
    consent_record: Mapped[ConsentRecord] = relationship()
