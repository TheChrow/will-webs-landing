from collections.abc import Callable, Coroutine
from typing import Annotated, Any
from urllib.parse import urlsplit

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import decode_access_token
from app.db.session import get_session
from app.models import AdminUser

SessionDep = Annotated[AsyncSession, Depends(get_session)]
_bearer = HTTPBearer(auto_error=False)

ROLE_ADMIN = "admin"
ROLE_EDITOR = "editor"


def _unauthorized() -> HTTPException:
    return HTTPException(
        status.HTTP_401_UNAUTHORIZED, "No autenticado", headers={"WWW-Authenticate": "Bearer"}
    )


async def get_current_user(
    session: SessionDep,
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> AdminUser:
    if creds is None:
        raise _unauthorized()
    try:
        payload = decode_access_token(creds.credentials)
    except jwt.PyJWTError:
        raise _unauthorized() from None
    user = (
        await session.execute(
            select(AdminUser)
            .options(selectinload(AdminUser.roles))
            .where(AdminUser.public_id == payload["sub"])
        )
    ).scalar_one_or_none()
    if user is None or not user.is_active:
        raise _unauthorized()
    return user


CurrentUser = Annotated[AdminUser, Depends(get_current_user)]


def require_roles(*roles: str) -> Callable[..., Coroutine[Any, Any, AdminUser]]:
    async def checker(user: CurrentUser) -> AdminUser:
        if not {r.name for r in user.roles} & set(roles):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Permisos insuficientes")
        return user

    return checker


AnyStaff = Annotated[AdminUser, Depends(require_roles(ROLE_ADMIN, ROLE_EDITOR))]
AdminOnly = Annotated[AdminUser, Depends(require_roles(ROLE_ADMIN))]


def check_same_origin(request: Request) -> None:
    """Defensa CSRF para endpoints que usan la cookie (además de SameSite=Strict)."""
    origin = request.headers.get("origin") or request.headers.get("referer")
    if not origin:
        return  # clientes no-navegador; la cookie SameSite=Strict ya limita el riesgo
    if urlsplit(origin).netloc != request.headers.get("host"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Origen no permitido")


def client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None
