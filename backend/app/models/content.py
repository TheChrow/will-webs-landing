from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    false,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import PK, AuditMixin, IdMixin, PublicIdMixin, SoftDeleteMixin, Timestamp


class PublishableMixin:
    sort_order: Mapped[int] = mapped_column(SmallInteger, server_default=text("0"), default=0)
    is_published: Mapped[bool] = mapped_column(Boolean, server_default=false(), default=False)


class ServiceCategory(IdMixin, PublicIdMixin, AuditMixin, SoftDeleteMixin, Base):
    __tablename__ = "service_category"

    slug: Mapped[str] = mapped_column(String(120), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    sort_order: Mapped[int] = mapped_column(SmallInteger, server_default=text("0"), default=0)

    services: Mapped[list["Service"]] = relationship(back_populates="category")


class Service(IdMixin, PublicIdMixin, PublishableMixin, AuditMixin, SoftDeleteMixin, Base):
    __tablename__ = "service"
    __table_args__ = (Index("ix_service_published_order", "is_published", "sort_order"),)

    category_id: Mapped[int | None] = mapped_column(
        PK, ForeignKey("service_category.id", ondelete="SET NULL"), nullable=True
    )
    slug: Mapped[str] = mapped_column(String(120), unique=True)
    title: Mapped[str] = mapped_column(String(120))
    summary: Mapped[str] = mapped_column(String(280))
    description: Mapped[str | None] = mapped_column(Text)
    icon: Mapped[str | None] = mapped_column(String(64))

    category: Mapped[ServiceCategory | None] = relationship(back_populates="services")


class Banner(IdMixin, PublicIdMixin, PublishableMixin, AuditMixin, SoftDeleteMixin, Base):
    __tablename__ = "banner"
    __table_args__ = (
        CheckConstraint(
            "ends_at IS NULL OR starts_at IS NULL OR ends_at > starts_at", name="valid_period"
        ),
        CheckConstraint("cta_label IS NULL OR cta_href IS NOT NULL", name="cta_requires_href"),
    )

    title: Mapped[str] = mapped_column(String(160))
    subtitle: Mapped[str | None] = mapped_column(String(280))
    image_url: Mapped[str | None] = mapped_column(String(500))
    image_alt: Mapped[str] = mapped_column(String(200))
    cta_label: Mapped[str | None] = mapped_column(String(60))
    cta_href: Mapped[str | None] = mapped_column(String(500))
    starts_at: Mapped[datetime | None] = mapped_column(Timestamp)
    ends_at: Mapped[datetime | None] = mapped_column(Timestamp)


class ClientCompany(IdMixin, PublicIdMixin, PublishableMixin, AuditMixin, SoftDeleteMixin, Base):
    __tablename__ = "client_company"

    name: Mapped[str] = mapped_column(String(160))
    logo_url: Mapped[str | None] = mapped_column(String(500))
    logo_alt: Mapped[str] = mapped_column(String(200))
    website_url: Mapped[str | None] = mapped_column(String(500))
    logo_consent_at: Mapped[datetime | None] = mapped_column(Timestamp)


class ContentBlock(IdMixin, AuditMixin, Base):
    __tablename__ = "content_block"
    __table_args__ = (UniqueConstraint("key", "locale", name="uq_content_block_key_locale"),)

    key: Mapped[str] = mapped_column(String(100))
    locale: Mapped[str] = mapped_column(String(10), server_default="es-CL", default="es-CL")
    title: Mapped[str | None] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text)
    is_published: Mapped[bool] = mapped_column(Boolean, server_default=false(), default=False)


class SiteSetting(IdMixin, AuditMixin, Base):
    __tablename__ = "site_setting"

    key: Mapped[str] = mapped_column(String(100), unique=True)
    value: Mapped[str] = mapped_column(Text)
    is_public: Mapped[bool] = mapped_column(Boolean, server_default=false(), default=False)
