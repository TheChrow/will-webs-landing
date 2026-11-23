"""Anonimización de leads (derecho de supresión y política de retención)."""

from sqlalchemy import ColumnElement, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.timeutil import utcnow
from app.models import ContactMessage

ANONYMIZED_NAME = "[anonimizado]"


async def anonymize_leads(session: AsyncSession, where: ColumnElement[bool]) -> int:
    """Borra los datos personales de los leads que cumplen `where`. No hace commit."""
    result = await session.execute(
        update(ContactMessage)
        .where(where, ContactMessage.anonymized_at.is_(None))
        .values(
            name=ANONYMIZED_NAME,
            # Email no reversible pero único por lead (anon+<public_id>@invalid).
            email="anon+" + ContactMessage.public_id + "@invalid",
            company=None,
            phone=None,
            message=None,
            ip_hash=None,
            user_agent=None,
            anonymized_at=utcnow(),
        )
        .execution_options(synchronize_session=False)
    )
    return result.rowcount or 0
