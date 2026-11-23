"""Verificación server-side de Cloudflare Turnstile."""

import logging

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


async def verify_captcha(token: str | None, remote_ip: str | None) -> bool:
    settings = get_settings()
    secret = settings.turnstile_secret_key.get_secret_value()
    if not secret:
        # Solo posible fuera de producción (config.py lo exige en prod).
        logger.warning("captcha desactivado: TURNSTILE_SECRET_KEY vacío")
        return True
    if not token:
        return False
    data = {"secret": secret, "response": token}
    if remote_ip:
        data["remoteip"] = remote_ip
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(settings.turnstile_verify_url, data=data)
            resp.raise_for_status()
            return bool(resp.json().get("success"))
    except (httpx.HTTPError, ValueError):
        logger.exception("captcha: error verificando el token")
        return False
