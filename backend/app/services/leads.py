from datetime import UTC, date, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.hashing import pseudonymize
from app.models import ConsentPurpose, ConsentRecord, ContactMessage, LegalDocumentType
from app.repositories import content as content_repo
from app.schemas.contact import ContactIn


class FormUnavailableError(Exception):
    """No hay Política de Privacidad vigente: no se pueden recoger datos personales."""


class UnknownServiceError(Exception):
    pass


def add_months(start: date, months: int) -> date:
    month_index = start.month - 1 + months
    year, month = start.year + month_index // 12, month_index % 12 + 1
    # Ajuste de fin de mes (31-ene + 1 mes -> 28/29-feb).
    for day in (start.day, 30, 29, 28):
        try:
            return date(year, month, day)
        except ValueError:
            continue
    raise AssertionError("unreachable")


async def create_lead(
    session: AsyncSession, data: ContactIn, client_ip: str | None, user_agent: str | None
) -> tuple[ContactMessage, str | None]:
    """Crea consentimiento(s) + lead en una transacción.

    Devuelve el lead y el título del servicio de interés (si hay).
    """
    legal = await content_repo.get_current_legal(session, LegalDocumentType.privacy)
    if legal is None:
        raise FormUnavailableError
    _, privacy_version = legal

    service_id = None
    service_title = None
    if data.service:
        service = await content_repo.get_service(session, data.service)
        if service is None:
            raise UnknownServiceError
        service_id, service_title = service.id, service.title

    ip_hash = pseudonymize(client_ip)
    email_hash = pseudonymize(data.email)

    consent = ConsentRecord(
        legal_document_version_id=privacy_version.id,
        purpose=ConsentPurpose.contact,
        granted=True,
        subject_email_hash=email_hash,
        ip_hash=ip_hash,
    )
    session.add(consent)
    if data.marketing_opt_in:
        session.add(
            ConsentRecord(
                legal_document_version_id=privacy_version.id,
                purpose=ConsentPurpose.marketing,
                granted=True,
                subject_email_hash=email_hash,
                ip_hash=ip_hash,
            )
        )
    await session.flush()

    today = datetime.now(UTC).date()
    lead = ContactMessage(
        name=data.name,
        email=data.email,
        company=data.company or None,
        phone=data.phone,
        service_id=service_id,
        message=data.message,
        consent_record_id=consent.id,
        ip_hash=ip_hash,
        user_agent=(user_agent or "")[:255] or None,
        retention_until=add_months(today, get_settings().lead_retention_months),
    )
    session.add(lead)
    await session.commit()
    return lead, service_title
