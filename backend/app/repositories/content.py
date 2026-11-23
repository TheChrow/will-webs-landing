"""Consultas de contenido público.

Solo SQLAlchemy con parámetros ligados: nunca SQL construido con strings.
"""

from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    Banner,
    ClientCompany,
    ContentBlock,
    LegalDocument,
    LegalDocumentType,
    LegalDocumentVersion,
    Service,
    SiteSetting,
)


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


async def list_services(session: AsyncSession) -> Sequence[Service]:
    stmt = (
        select(Service)
        .options(selectinload(Service.category))
        .where(Service.is_published.is_(True), Service.deleted_at.is_(None))
        .order_by(Service.sort_order, Service.id)
    )
    return (await session.execute(stmt)).scalars().all()


async def get_service(session: AsyncSession, slug: str) -> Service | None:
    stmt = (
        select(Service)
        .options(selectinload(Service.category))
        .where(
            Service.slug == slug,
            Service.is_published.is_(True),
            Service.deleted_at.is_(None),
        )
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def list_banners(session: AsyncSession) -> Sequence[Banner]:
    now = _utcnow()
    stmt = (
        select(Banner)
        .where(
            Banner.is_published.is_(True),
            Banner.deleted_at.is_(None),
            or_(Banner.starts_at.is_(None), Banner.starts_at <= now),
            or_(Banner.ends_at.is_(None), Banner.ends_at > now),
        )
        .order_by(Banner.sort_order, Banner.id)
    )
    return (await session.execute(stmt)).scalars().all()


async def list_clients(session: AsyncSession) -> Sequence[ClientCompany]:
    stmt = (
        select(ClientCompany)
        .where(
            ClientCompany.is_published.is_(True),
            ClientCompany.deleted_at.is_(None),
            # Sin autorización de uso de marca no se publica el logo.
            ClientCompany.logo_consent_at.is_not(None),
        )
        .order_by(ClientCompany.sort_order, ClientCompany.id)
    )
    return (await session.execute(stmt)).scalars().all()


async def list_content(
    session: AsyncSession, locale: str, prefix: str | None
) -> Sequence[ContentBlock]:
    stmt = select(ContentBlock).where(
        ContentBlock.locale == locale, ContentBlock.is_published.is_(True)
    )
    if prefix:
        # startswith escapa % y _ -> sin comodines inyectados.
        stmt = stmt.where(ContentBlock.key.startswith(prefix, autoescape=True))
    return (await session.execute(stmt.order_by(ContentBlock.key))).scalars().all()


async def get_content(session: AsyncSession, key: str, locale: str) -> ContentBlock | None:
    stmt = select(ContentBlock).where(
        ContentBlock.key == key,
        ContentBlock.locale == locale,
        ContentBlock.is_published.is_(True),
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def get_current_legal(
    session: AsyncSession, doc_type: LegalDocumentType
) -> tuple[LegalDocument, LegalDocumentVersion] | None:
    stmt = (
        select(LegalDocument, LegalDocumentVersion)
        .join(LegalDocumentVersion, LegalDocumentVersion.document_id == LegalDocument.id)
        .where(
            LegalDocument.type == doc_type,
            LegalDocumentVersion.is_current.is_(True),
            LegalDocumentVersion.published_at.is_not(None),
        )
        .order_by(LegalDocumentVersion.published_at.desc())
        .limit(1)
    )
    row = (await session.execute(stmt)).first()
    return (row[0], row[1]) if row else None


async def public_settings(session: AsyncSession) -> dict[str, str]:
    stmt = select(SiteSetting.key, SiteSetting.value).where(SiteSetting.is_public.is_(True))
    return {k: v for k, v in (await session.execute(stmt)).all()}


async def get_published_service_id(session: AsyncSession, slug: str) -> int | None:
    stmt = select(Service.id).where(
        Service.slug == slug, Service.is_published.is_(True), Service.deleted_at.is_(None)
    )
    return (await session.execute(stmt)).scalar_one_or_none()
