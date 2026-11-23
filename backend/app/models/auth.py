from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, Column, ForeignKey, SmallInteger, String, Table, text, true
from sqlalchemy.dialects.mysql import BINARY, VARBINARY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import PK, AuditMixin, CreatedAtMixin, IdMixin, PublicIdMixin, Timestamp

admin_user_role = Table(
    "admin_user_role",
    Base.metadata,
    Column("admin_user_id", PK, ForeignKey("admin_user.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", PK, ForeignKey("role.id", ondelete="CASCADE"), primary_key=True),
)


class Role(IdMixin, AuditMixin, Base):
    __tablename__ = "role"

    name: Mapped[str] = mapped_column(String(50), unique=True)
    description: Mapped[str | None] = mapped_column(String(255))


class AdminUser(IdMixin, PublicIdMixin, AuditMixin, Base):
    __tablename__ = "admin_user"

    email: Mapped[str] = mapped_column(String(254), unique=True)
    full_name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=true(), default=True)
    mfa_secret_enc: Mapped[bytes | None] = mapped_column(VARBINARY(255))
    failed_attempts: Mapped[int] = mapped_column(SmallInteger, server_default=text("0"), default=0)
    locked_until: Mapped[datetime | None] = mapped_column(Timestamp)
    last_login_at: Mapped[datetime | None] = mapped_column(Timestamp)

    roles: Mapped[list[Role]] = relationship(secondary=admin_user_role)


class RefreshToken(IdMixin, CreatedAtMixin, Base):
    __tablename__ = "refresh_token"

    admin_user_id: Mapped[int] = mapped_column(PK, ForeignKey("admin_user.id", ondelete="CASCADE"))
    token_hash: Mapped[bytes] = mapped_column(BINARY(32), unique=True)
    expires_at: Mapped[datetime] = mapped_column(Timestamp)
    revoked_at: Mapped[datetime | None] = mapped_column(Timestamp)
    replaced_by_id: Mapped[int | None] = mapped_column(
        PK, ForeignKey("refresh_token.id", ondelete="SET NULL")
    )
    user_agent: Mapped[str | None] = mapped_column(String(255))
    ip_hash: Mapped[bytes | None] = mapped_column(BINARY(32))


class AuditLog(IdMixin, CreatedAtMixin, Base):
    """Append-only."""

    __tablename__ = "audit_log"

    actor_id: Mapped[int | None] = mapped_column(
        PK, ForeignKey("admin_user.id", ondelete="SET NULL"), index=True
    )
    action: Mapped[str] = mapped_column(String(50))
    entity: Mapped[str] = mapped_column(String(50))
    entity_id: Mapped[str | None] = mapped_column(String(26))
    diff: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    ip_hash: Mapped[bytes | None] = mapped_column(BINARY(32))
