"""Seudonimización de datos personales (IP, email) con HMAC-SHA256 + pepper."""

import hashlib
import hmac

from app.core.config import get_settings


def pseudonymize(value: str | None) -> bytes | None:
    if not value:
        return None
    pepper = get_settings().hash_pepper.get_secret_value().encode()
    return hmac.new(pepper, value.strip().lower().encode(), hashlib.sha256).digest()
