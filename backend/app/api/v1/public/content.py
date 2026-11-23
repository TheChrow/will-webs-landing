from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models import LegalDocumentType
from app.repositories import content as repo
from app.schemas.public import (
    BannerOut,
    ClientOut,
    ContentBlockOut,
    LegalDocumentOut,
    ServiceOut,
)

SessionDep = Annotated[AsyncSession, Depends(get_session)]
Slug = Annotated[str, Path(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$", max_length=120)]
ContentKey = Annotated[str, Path(pattern=r"^[a-z0-9]+(\.[a-z0-9_]+)+$", max_length=100)]
Locale = Annotated[str, Query(pattern=r"^[a-z]{2}(-[A-Z]{2})?$")]


def _cache(response: Response) -> None:
    # Contenido público: cacheable por navegador y proxy durante 5 minutos.
    response.headers["Cache-Control"] = "public, max-age=300"


router = APIRouter(tags=["public"], dependencies=[Depends(_cache)])


@router.get("/services", response_model=list[ServiceOut])
async def list_services(session: SessionDep) -> list[ServiceOut]:
    return [ServiceOut.model_validate(s) for s in await repo.list_services(session)]


@router.get("/services/{slug}", response_model=ServiceOut)
async def get_service(slug: Slug, session: SessionDep) -> ServiceOut:
    service = await repo.get_service(session, slug)
    if service is None:
        raise HTTPException(404, "Servicio no encontrado")
    return ServiceOut.model_validate(service)


@router.get("/banners", response_model=list[BannerOut])
async def list_banners(session: SessionDep) -> list[BannerOut]:
    return [BannerOut.model_validate(b) for b in await repo.list_banners(session)]


@router.get("/clients", response_model=list[ClientOut])
async def list_clients(session: SessionDep) -> list[ClientOut]:
    return [ClientOut.model_validate(c) for c in await repo.list_clients(session)]


@router.get("/content", response_model=list[ContentBlockOut])
async def list_content(
    session: SessionDep,
    locale: Locale = "es-CL",
    prefix: Annotated[str | None, Query(pattern=r"^[a-z0-9._]+$", max_length=100)] = None,
) -> list[ContentBlockOut]:
    blocks = await repo.list_content(session, locale, prefix)
    return [ContentBlockOut.model_validate(b) for b in blocks]


@router.get("/content/{key}", response_model=ContentBlockOut)
async def get_content(
    key: ContentKey, session: SessionDep, locale: Locale = "es-CL"
) -> ContentBlockOut:
    block = await repo.get_content(session, key, locale)
    if block is None:
        raise HTTPException(404, "Contenido no encontrado")
    return ContentBlockOut.model_validate(block)


@router.get("/legal/{doc_type}", response_model=LegalDocumentOut)
async def get_legal(doc_type: LegalDocumentType, session: SessionDep) -> LegalDocumentOut:
    found = await repo.get_current_legal(session, doc_type)
    if found is None:
        raise HTTPException(404, "Documento legal no publicado")
    doc, version = found
    return LegalDocumentOut(
        type=doc.type,
        slug=doc.slug,
        title=doc.title,
        version=version.version,
        body=version.body,
        published_at=version.published_at,
    )


@router.get("/settings", response_model=dict[str, str])
async def get_settings_public(session: SessionDep) -> dict[str, str]:
    return await repo.public_settings(session)
