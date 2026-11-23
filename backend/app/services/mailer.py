"""Notificación por correo de nuevos leads (se ejecuta en background, fuera del request)."""

import logging
import smtplib
import ssl
from dataclasses import dataclass
from email.message import EmailMessage
from email.utils import formataddr

from app.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LeadNotification:
    public_id: str
    name: str
    email: str
    company: str | None
    phone: str | None
    service: str | None
    message: str


def build_message(lead: LeadNotification) -> EmailMessage:
    settings = get_settings()
    msg = EmailMessage()
    msg["From"] = settings.mail_from
    msg["To"] = settings.leads_notify_to
    # Los campos ya vienen validados sin saltos de línea; EmailMessage además rechaza CR/LF.
    msg["Subject"] = f"Nuevo contacto web: {lead.name}"
    msg["Reply-To"] = formataddr((lead.name, lead.email))
    msg.set_content(
        "Nuevo mensaje desde el formulario de contacto\n"
        f"ID: {lead.public_id}\n"
        f"Nombre: {lead.name}\n"
        f"Email: {lead.email}\n"
        f"Empresa: {lead.company or '-'}\n"
        f"Teléfono: {lead.phone or '-'}\n"
        f"Servicio de interés: {lead.service or '-'}\n\n"
        f"Mensaje:\n{lead.message}\n"
    )
    return msg


def send_lead_notification(lead: LeadNotification) -> None:
    settings = get_settings()
    msg = build_message(lead)
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
            if settings.smtp_starttls:
                smtp.starttls(context=ssl.create_default_context())
            if settings.smtp_user:
                smtp.login(settings.smtp_user, settings.smtp_password.get_secret_value())
            smtp.send_message(msg)
    except (OSError, smtplib.SMTPException):
        # El lead ya está guardado: un fallo de correo no se propaga al usuario.
        logger.exception("no se pudo enviar la notificación del lead %s", lead.public_id)
