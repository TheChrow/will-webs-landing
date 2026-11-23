"""Bandeja de leads y derechos del titular (acceso / supresión)."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.api.v1.admin.deps import AdminOnly, AnyStaff, SessionDep, client_ip
from app.core.hashing import pseudonymize
from app.models import (
    ConsentRecord,
    ContactMessage,
    ContactStatus,
    LegalDocumentVersion,
)
from app.schemas.admin import (
    AnonymizeOut,
    ConsentOut,
    DataSubjectIn,
    DataSubjectOut,
    LeadOut,
    LeadPatch,
    Page,
)
from app.services import audit
from app.services.privacy import anonymize_leads

router = APIRouter(tags=["admin-leads"])

PublicId = Annotated[str, Path(pattern=r"^[0-9A-HJKMNP-TV-Z]{26}$")]


def _lead_out(m: ContactMessage) -> LeadOut:
    return LeadOut(
        id=m.public_id,
        name=m.name,
        email=m.email,
        company=m.company,
        phone=m.phone,
        service=m.service.title if m.service else None,
        message=m.message,
        status=m.status,
        created_at=m.created_at,
        retention_until=m.retention_until,
        anonymized_at=m.anonymized_at,
    )


@router.get("/leads", response_model=Page[LeadOut])
async def list_leads(
    _: AnyStaff,
    session: SessionDep,
    lead_status: Annotated[ContactStatus | None, Query(alias="status")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    offset: Annotated[int, Query(ge=0, le=100_000)] = 0,
) -> Page[LeadOut]:
    base = select(ContactMessage)
    if lead_status is not None:
        base = base.where(ContactMessage.status == lead_status)
    total = (await session.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
    rows = (
        await session.execute(
            base.options(selectinload(ContactMessage.service))
            .order_by(ContactMessage.id.desc())
            .limit(limit)
            .offset(offset)
        )
    ).scalars()
    return Page[LeadOut](
        items=[_lead_out(m) for m in rows], total=total, limit=limit, offset=offset
    )


async def _get_lead(session: SessionDep, public_id: str) -> ContactMessage:
    lead = (
        await session.execute(
            select(ContactMessage)
            .options(selectinload(ContactMessage.service))
            .where(ContactMessage.public_id == public_id)
        )
    ).scalar_one_or_none()
    if lead is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lead no encontrado")
    return lead


@router.get("/leads/{public_id}", response_model=LeadOut)
async def get_lead(public_id: PublicId, _: AnyStaff, session: SessionDep) -> LeadOut:
    return _lead_out(await _get_lead(session, public_id))


@router.patch("/leads/{public_id}", response_model=LeadOut)
async def update_lead(
    public_id: PublicId, data: LeadPatch, user: AnyStaff, session: SessionDep, request: Request
) -> LeadOut:
    lead = await _get_lead(session, public_id)
    if lead.status != data.status:
        audit.record(
            session,
            actor=user,
            action="update",
            entity="contact_message",
            entity_id=public_id,
            diff={"status": [lead.status, data.status]},
            ip=client_ip(request),
        )
        lead.status = data.status
        lead.updated_by = user.id
        await session.commit()
        lead = await _get_lead(session, public_id)
    return _lead_out(lead)


# ---------- Derechos del titular (solo admin) ----------


@router.post("/data-subject/export", response_model=DataSubjectOut)
async def export_subject(
    data: DataSubjectIn, user: AdminOnly, session: SessionDep, request: Request
) -> DataSubjectOut:
    """Derecho de acceso: datos asociados a un email (POST: el email no queda en URLs/logs)."""
    leads = (
        (
            await session.execute(
                select(ContactMessage)
                .options(selectinload(ContactMessage.service))
                .where(ContactMessage.email == data.email)
                .order_by(ContactMessage.id)
            )
        )
        .scalars()
        .all()
    )
    consents = (
        (
            await session.execute(
                select(ConsentRecord)
                .options(
                    selectinload(ConsentRecord.legal_document_version).selectinload(
                        LegalDocumentVersion.document
                    )
                )
                .where(ConsentRecord.subject_email_hash == pseudonymize(data.email))
                .order_by(ConsentRecord.id)
            )
        )
        .scalars()
        .all()
    )
    audit.record(
        session,
        actor=user,
        action="data_subject_export",
        entity="contact_message",
        diff={"leads": len(leads), "consents": len(consents)},
        ip=client_ip(request),
    )
    await session.commit()
    return DataSubjectOut(
        email=data.email,
        leads=[_lead_out(m) for m in leads],
        consents=[
            ConsentOut(
                purpose=c.purpose,
                granted=c.granted,
                created_at=c.created_at,
                document=c.legal_document_version.document.type,
                version=c.legal_document_version.version,
            )
            for c in consents
        ],
    )


@router.post("/data-subject/anonymize", response_model=AnonymizeOut)
async def anonymize_subject(
    data: DataSubjectIn, user: AdminOnly, session: SessionDep, request: Request
) -> AnonymizeOut:
    """Derecho de supresión: anonimiza leads; los consentimientos (hashes) quedan como prueba."""
    count = await anonymize_leads(session, ContactMessage.email == data.email)
    audit.record(
        session,
        actor=user,
        action="data_subject_anonymize",
        entity="contact_message",
        diff={"anonymized": count},
        ip=client_ip(request),
    )
    await session.commit()
    return AnonymizeOut(anonymized=count)
