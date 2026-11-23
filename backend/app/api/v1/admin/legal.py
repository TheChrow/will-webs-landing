"""Documentos legales versionados.

Una versión publicada es inmutable: es la prueba de lo que aceptó cada titular.
"""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query, Request, status
from sqlalchemy import func, select, update
from sqlalchemy.orm import selectinload

from app.api.v1.admin.deps import AdminOnly, SessionDep, client_ip
from app.core.timeutil import utcnow
from app.models import AdminUser, AuditLog, LegalDocument, LegalDocumentType, LegalDocumentVersion
from app.schemas.admin import (
    AuditOut,
    LegalBodyPatch,
    LegalDocumentAdminOut,
    LegalVersionIn,
    LegalVersionOut,
    Page,
)
from app.services import audit

router = APIRouter(tags=["admin-legal"])

Version = Annotated[str, Path(pattern=r"^\d{1,3}\.\d{1,3}\.\d{1,3}$")]


def _version_out(v: LegalDocumentVersion, with_body: bool = False) -> LegalVersionOut:
    return LegalVersionOut(
        version=v.version,
        is_current=v.is_current,
        published_at=v.published_at,
        created_at=v.created_at,
        body=v.body if with_body else None,
    )


async def _doc(session: SessionDep, doc_type: LegalDocumentType) -> LegalDocument:
    doc = (
        await session.execute(
            select(LegalDocument)
            .options(selectinload(LegalDocument.versions))
            .where(LegalDocument.type == doc_type)
        )
    ).scalar_one_or_none()
    if doc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Documento no encontrado")
    return doc


def _find(doc: LegalDocument, version: str) -> LegalDocumentVersion:
    for v in doc.versions:
        if v.version == version:
            return v
    raise HTTPException(status.HTTP_404_NOT_FOUND, "Versión no encontrada")


@router.get("/legal", response_model=list[LegalDocumentAdminOut])
async def list_legal(_: AdminOnly, session: SessionDep) -> list[LegalDocumentAdminOut]:
    docs = (
        await session.execute(
            select(LegalDocument)
            .options(selectinload(LegalDocument.versions))
            .order_by(LegalDocument.id)
        )
    ).scalars()
    return [
        LegalDocumentAdminOut(
            type=d.type,
            slug=d.slug,
            title=d.title,
            versions=[
                _version_out(v) for v in sorted(d.versions, key=lambda v: v.id, reverse=True)
            ],
        )
        for d in docs
    ]


@router.get("/legal/{doc_type}/versions/{version}", response_model=LegalVersionOut)
async def get_version(
    doc_type: LegalDocumentType, version: Version, _: AdminOnly, session: SessionDep
) -> LegalVersionOut:
    return _version_out(_find(await _doc(session, doc_type), version), with_body=True)


@router.post(
    "/legal/{doc_type}/versions",
    response_model=LegalVersionOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_version(
    doc_type: LegalDocumentType,
    data: LegalVersionIn,
    user: AdminOnly,
    session: SessionDep,
    request: Request,
) -> LegalVersionOut:
    doc = await _doc(session, doc_type)
    if any(v.version == data.version for v in doc.versions):
        raise HTTPException(status.HTTP_409_CONFLICT, "La versión ya existe")
    version = LegalDocumentVersion(
        document_id=doc.id,
        version=data.version,
        body=data.body,
        created_by=user.id,
        updated_by=user.id,
    )
    session.add(version)
    audit.record(
        session,
        actor=user,
        action="create",
        entity="legal_document_version",
        entity_id=f"{doc_type.value}:{data.version}",
        ip=client_ip(request),
    )
    await session.commit()
    await session.refresh(version)
    return _version_out(version, with_body=True)


@router.patch("/legal/{doc_type}/versions/{version}", response_model=LegalVersionOut)
async def update_draft(
    doc_type: LegalDocumentType,
    version: Version,
    data: LegalBodyPatch,
    user: AdminOnly,
    session: SessionDep,
    request: Request,
) -> LegalVersionOut:
    v = _find(await _doc(session, doc_type), version)
    if v.published_at is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Una versión publicada no se modifica: crea una nueva versión",
        )
    v.body = data.body
    v.updated_by = user.id
    audit.record(
        session,
        actor=user,
        action="update",
        entity="legal_document_version",
        entity_id=f"{doc_type.value}:{version}",
        ip=client_ip(request),
    )
    await session.commit()
    await session.refresh(v)
    return _version_out(v, with_body=True)


@router.post("/legal/{doc_type}/versions/{version}/publish", response_model=LegalVersionOut)
async def publish_version(
    doc_type: LegalDocumentType,
    version: Version,
    user: AdminOnly,
    session: SessionDep,
    request: Request,
) -> LegalVersionOut:
    doc = await _doc(session, doc_type)
    v = _find(doc, version)
    if v.is_current:
        return _version_out(v, with_body=True)
    await session.execute(
        update(LegalDocumentVersion)
        .where(LegalDocumentVersion.document_id == doc.id)
        .values(is_current=False)
        .execution_options(synchronize_session=False)
    )
    v.is_current = True
    v.published_at = v.published_at or utcnow()
    v.updated_by = user.id
    audit.record(
        session,
        actor=user,
        action="publish",
        entity="legal_document_version",
        entity_id=f"{doc_type.value}:{version}",
        ip=client_ip(request),
    )
    await session.commit()
    await session.refresh(v)
    return _version_out(v, with_body=True)


# ---------- Auditoría ----------


@router.get("/audit", response_model=Page[AuditOut])
async def list_audit(
    _: AdminOnly,
    session: SessionDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0, le=100_000)] = 0,
) -> Page[AuditOut]:
    total = (await session.execute(select(func.count()).select_from(AuditLog))).scalar_one()
    rows = (
        await session.execute(
            select(AuditLog, AdminUser.email)
            .outerjoin(AdminUser, AdminUser.id == AuditLog.actor_id)
            .order_by(AuditLog.id.desc())
            .limit(limit)
            .offset(offset)
        )
    ).all()
    return Page[AuditOut](
        items=[
            AuditOut(
                action=a.action,
                entity=a.entity,
                entity_id=a.entity_id,
                actor=email,
                diff=a.diff,
                created_at=a.created_at,
            )
            for a, email in rows
        ],
        total=total,
        limit=limit,
        offset=offset,
    )
