"""Job de retención (ejecutar a diario):
    docker compose ... run --rm backend python -m app.jobs.retention

- Anonimiza leads con retention_until vencido.
- Borra refresh tokens expirados hace más de 30 días.
- Borra audit log más antiguo que AUDIT_RETENTION_MONTHS.
"""

import asyncio
import logging
from datetime import timedelta

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import get_settings
from app.core.timeutil import utcnow
from app.db.session import dispose_engine, get_engine
from app.models import AuditLog, ContactMessage, RefreshToken
from app.services import audit
from app.services.leads import add_months
from app.services.privacy import anonymize_leads

logger = logging.getLogger("retention")


async def run_retention(session: AsyncSession) -> dict[str, int]:
    now = utcnow()
    leads = await anonymize_leads(session, ContactMessage.retention_until < now.date())
    tokens = (
        await session.execute(
            delete(RefreshToken).where(RefreshToken.expires_at < now - timedelta(days=30))
        )
    ).rowcount or 0
    audit_cutoff = add_months(now.date(), -get_settings().audit_retention_months)
    audits = (
        await session.execute(delete(AuditLog).where(AuditLog.created_at < audit_cutoff))
    ).rowcount or 0
    result = {"leads_anonymized": leads, "refresh_tokens_deleted": tokens, "audit_deleted": audits}
    audit.record(session, actor=None, action="retention_job", entity="system", diff=result)
    await session.commit()
    return result


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s [%(name)s] %(message)s")
    async with async_sessionmaker(get_engine())() as session:
        result = await run_retention(session)
    await dispose_engine()
    logger.info("retención aplicada: %s", result)


if __name__ == "__main__":
    asyncio.run(main())
