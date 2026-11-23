"""Contraseñas (Argon2id), JWT de acceso y refresh tokens opacos."""

import hashlib
import secrets
from datetime import timedelta
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from app.core.config import get_settings
from app.core.timeutil import utcnow

# Parámetros por defecto de argon2-cffi (RFC 9106, perfil de baja memoria): Argon2id.
_hasher = PasswordHasher()
# Hash de relleno para igualar el tiempo de respuesta cuando el usuario no existe.
_DUMMY_HASH = _hasher.hash(secrets.token_urlsafe(16))

MIN_PASSWORD_LENGTH = 12
JWT_ALGORITHM = "HS256"
JWT_ISSUER = "willwebs"
JWT_AUDIENCE = "willwebs-admin"


def hash_password(password: str) -> str:
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"La contraseña debe tener al menos {MIN_PASSWORD_LENGTH} caracteres")
    return _hasher.hash(password)


def verify_password(password_hash: str | None, password: str) -> bool:
    try:
        return _hasher.verify(password_hash or _DUMMY_HASH, password) and password_hash is not None
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def needs_rehash(password_hash: str) -> bool:
    return _hasher.check_needs_rehash(password_hash)


def create_access_token(subject: str, roles: list[str]) -> tuple[str, int]:
    settings = get_settings()
    now = utcnow()
    ttl = timedelta(minutes=settings.access_token_minutes)
    payload = {
        "sub": subject,
        "roles": roles,
        "type": "access",
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
        "iat": now,
        "exp": now + ttl,
        "jti": secrets.token_hex(8),
    }
    token = jwt.encode(payload, settings.jwt_secret.get_secret_value(), algorithm=JWT_ALGORITHM)
    return token, int(ttl.total_seconds())


def decode_access_token(token: str) -> dict[str, Any]:
    """Lanza jwt.PyJWTError si el token es inválido o expiró."""
    payload = jwt.decode(
        token,
        get_settings().jwt_secret.get_secret_value(),
        algorithms=[JWT_ALGORITHM],  # nunca aceptar el algoritmo que diga el token
        audience=JWT_AUDIENCE,
        issuer=JWT_ISSUER,
        options={"require": ["exp", "iat", "sub"]},
    )
    if payload.get("type") != "access":
        raise jwt.InvalidTokenError("tipo de token inválido")
    return payload


def new_refresh_token() -> tuple[str, bytes]:
    """Token opaco de 256 bits. En la base solo se guarda su SHA-256."""
    raw = secrets.token_urlsafe(32)
    return raw, hash_refresh_token(raw)


def hash_refresh_token(raw: str) -> bytes:
    return hashlib.sha256(raw.encode()).digest()
