from datetime import datetime

from sqlalchemy import CHAR, BigInteger, ForeignKey, text
from sqlalchemy.dialects.mysql import BIGINT, DATETIME
from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from app.core.ids import new_ulid

# BIGINT UNSIGNED en MySQL; BigInteger genérico en otros dialectos.
PK = BigInteger().with_variant(BIGINT(unsigned=True), "mysql")
Timestamp = DATETIME(fsp=6)


class IdMixin:
    id: Mapped[int] = mapped_column(PK, primary_key=True, autoincrement=True)


class PublicIdMixin:
    public_id: Mapped[str] = mapped_column(CHAR(26), unique=True, default=new_ulid)


class CreatedAtMixin:
    created_at: Mapped[datetime] = mapped_column(
        Timestamp, server_default=text("CURRENT_TIMESTAMP(6)"), nullable=False
    )


class AuditMixin(CreatedAtMixin):
    updated_at: Mapped[datetime] = mapped_column(
        Timestamp,
        # MySQL mantiene updated_at automáticamente.
        server_default=text("CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)"),
        nullable=False,
    )

    @declared_attr
    def created_by(cls) -> Mapped[int | None]:
        return mapped_column(PK, ForeignKey("admin_user.id", ondelete="SET NULL"), nullable=True)

    @declared_attr
    def updated_by(cls) -> Mapped[int | None]:
        return mapped_column(PK, ForeignKey("admin_user.id", ondelete="SET NULL"), nullable=True)


class SoftDeleteMixin:
    deleted_at: Mapped[datetime | None] = mapped_column(Timestamp, nullable=True)
