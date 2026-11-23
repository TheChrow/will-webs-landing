import logging
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.hashing import pseudonymize
from app.core.ratelimit import limiter
from app.db.session import get_session
from app.schemas.contact import ContactAccepted, ContactIn
from app.services import captcha, leads, mailer

router = APIRouter(tags=["contact"])
logger = logging.getLogger(__name__)

_WINDOW_SECONDS = 3600


def _rate_limit(key: str, limit: int) -> None:
    retry_after = limiter.hit(key, limit, _WINDOW_SECONDS)
    if retry_after is not None:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Demasiados envíos. Intenta más tarde.",
            headers={"Retry-After": str(retry_after)},
        )


@router.post(
    "/contact",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=ContactAccepted,
    responses={
        429: {"description": "Rate limit excedido"},
        400: {"description": "Captcha inválido"},
    },
)
async def submit_contact(
    data: ContactIn,
    request: Request,
    background: BackgroundTasks,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ContactAccepted:
    settings = get_settings()
    client_ip = request.client.host if request.client else None
    ip_key = (pseudonymize(client_ip) or b"unknown").hex()

    _rate_limit(f"contact:ip:{ip_key}", settings.contact_rate_limit_per_hour)

    # Bots: honeypot lleno o envío instantáneo. Se responde igual que un éxito
    # para no dar señales, pero no se guarda nada.
    if data.website or data.elapsed_ms < settings.contact_min_fill_seconds * 1000:
        logger.info("contacto descartado como bot (ip_key=%s)", ip_key[:12])
        return ContactAccepted()

    if not await captcha.verify_captcha(data.captcha_token, client_ip):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Verificación anti-bot fallida")

    email_key = (pseudonymize(data.email) or b"").hex()
    _rate_limit(f"contact:email:{email_key}", settings.contact_rate_limit_per_hour)

    try:
        lead, service_title = await leads.create_lead(
            session, data, client_ip, request.headers.get("user-agent")
        )
    except leads.FormUnavailableError:
        logger.error("formulario de contacto sin Política de Privacidad vigente")
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "Formulario temporalmente no disponible"
        ) from None
    except leads.UnknownServiceError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Servicio desconocido") from None

    background.add_task(
        mailer.send_lead_notification,
        mailer.LeadNotification(
            public_id=lead.public_id,
            name=data.name,
            email=data.email,
            company=data.company,
            phone=data.phone,
            service=service_title,
            message=data.message,
        ),
    )
    return ContactAccepted()
