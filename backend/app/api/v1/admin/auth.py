import logging
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.api.v1.admin.deps import CurrentUser, SessionDep, check_same_origin, client_ip
from app.core.config import get_settings
from app.core.hashing import pseudonymize
from app.core.ratelimit import limiter
from app.core.security import (
    create_access_token,
    hash_password,
    hash_refresh_token,
    needs_rehash,
    new_refresh_token,
    verify_password,
)
from app.core.timeutil import utcnow
from app.models import AdminUser, RefreshToken
from app.schemas.admin import AdminUserOut, LoginIn, TokenOut
from app.services import audit

router = APIRouter(prefix="/auth", tags=["admin-auth"])
logger = logging.getLogger(__name__)

COOKIE_NAME = "ww_refresh"
COOKIE_PATH = "/api/v1/admin/auth"
_INVALID = "Credenciales inválidas"


def _user_out(user: AdminUser) -> AdminUserOut:
    return AdminUserOut(
        id=user.public_id,
        email=user.email,
        full_name=user.full_name,
        roles=sorted(r.name for r in user.roles),
    )


def _set_refresh_cookie(response: Response, raw: str) -> None:
    settings = get_settings()
    response.set_cookie(
        COOKIE_NAME,
        raw,
        max_age=settings.refresh_token_days * 86400,
        path=COOKIE_PATH,
        httponly=True,
        secure=settings.is_production,
        samesite="strict",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        COOKIE_NAME,
        path=COOKIE_PATH,
        httponly=True,
        secure=get_settings().is_production,
        samesite="strict",
    )


def _clear_cookie_headers() -> dict[str, str]:
    """Set-Cookie de borrado para una HTTPException (el Response inyectado se descarta)."""
    tmp = Response()
    _clear_refresh_cookie(tmp)
    return {"set-cookie": tmp.headers["set-cookie"]}


async def _issue_tokens(
    session: SessionDep, user: AdminUser, request: Request, response: Response
) -> tuple[TokenOut, RefreshToken]:
    raw, token_hash = new_refresh_token()
    refresh = RefreshToken(
        admin_user_id=user.id,
        token_hash=token_hash,
        expires_at=utcnow() + timedelta(days=get_settings().refresh_token_days),
        user_agent=(request.headers.get("user-agent") or "")[:255] or None,
        ip_hash=pseudonymize(client_ip(request)),
    )
    session.add(refresh)
    await session.flush()
    _set_refresh_cookie(response, raw)
    access, ttl = create_access_token(user.public_id, sorted(r.name for r in user.roles))
    return TokenOut(access_token=access, expires_in=ttl, user=_user_out(user)), refresh


@router.post("/login", response_model=TokenOut)
async def login(
    data: LoginIn, request: Request, response: Response, session: SessionDep
) -> TokenOut:
    settings = get_settings()
    ip = client_ip(request)
    ip_key = (pseudonymize(ip) or b"").hex()
    retry = limiter.hit(f"login:ip:{ip_key}", 10, 15 * 60)
    if retry is not None:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Demasiados intentos. Intenta más tarde.",
            headers={"Retry-After": str(retry)},
        )

    user = (
        await session.execute(
            select(AdminUser)
            .options(selectinload(AdminUser.roles))
            .where(AdminUser.email == data.email)
        )
    ).scalar_one_or_none()

    now = utcnow()
    if user is None or not user.is_active:
        verify_password(None, data.password)  # mismo costo de tiempo
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, _INVALID)

    if user.locked_until and user.locked_until > now:
        # Mismo mensaje: no confirmar que la cuenta existe ni que está bloqueada.
        verify_password(None, data.password)
        audit.record(
            session,
            actor=None,
            action="login_locked",
            entity="admin_user",
            entity_id=user.public_id,
            ip=ip,
        )
        await session.commit()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, _INVALID)

    if not verify_password(user.password_hash, data.password):
        user.failed_attempts += 1
        diff = {"failed_attempts": user.failed_attempts}
        if user.failed_attempts >= settings.login_max_attempts:
            user.locked_until = now + timedelta(minutes=settings.login_lock_minutes)
            user.failed_attempts = 0
            diff["locked_until"] = user.locked_until
        audit.record(
            session,
            actor=None,
            action="login_failed",
            entity="admin_user",
            entity_id=user.public_id,
            diff=diff,
            ip=ip,
        )
        await session.commit()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, _INVALID)

    user.failed_attempts = 0
    user.locked_until = None
    user.last_login_at = now
    if needs_rehash(user.password_hash):
        user.password_hash = hash_password(data.password)
    tokens, _ = await _issue_tokens(session, user, request, response)
    audit.record(
        session, actor=user, action="login", entity="admin_user", entity_id=user.public_id, ip=ip
    )
    await session.commit()
    return tokens


@router.post("/refresh", response_model=TokenOut, dependencies=[Depends(check_same_origin)])
async def refresh(
    request: Request,
    response: Response,
    session: SessionDep,
    ww_refresh: Annotated[str | None, Cookie()] = None,
) -> TokenOut:
    def fail() -> HTTPException:
        return HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Sesión expirada", headers=_clear_cookie_headers()
        )

    if not ww_refresh:
        raise fail()
    current = (
        await session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(ww_refresh))
        )
    ).scalar_one_or_none()
    if current is None:
        raise fail()

    now = utcnow()
    if current.revoked_at is not None:
        # Reutilización de un token ya rotado => posible robo: se revoca toda la familia.
        await session.execute(
            update(RefreshToken)
            .where(
                RefreshToken.admin_user_id == current.admin_user_id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )
        audit.record(
            session,
            actor=None,
            action="refresh_reuse_detected",
            entity="admin_user",
            ip=client_ip(request),
        )
        await session.commit()
        logger.warning("reutilización de refresh token: sesiones revocadas")
        raise fail()
    if current.expires_at <= now:
        raise fail()

    user = (
        await session.execute(
            select(AdminUser)
            .options(selectinload(AdminUser.roles))
            .where(AdminUser.id == current.admin_user_id)
        )
    ).scalar_one()
    if not user.is_active:
        raise fail()

    tokens, new = await _issue_tokens(session, user, request, response)
    current.revoked_at = now
    current.replaced_by_id = new.id
    await session.commit()
    return tokens


@router.post(
    "/logout", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(check_same_origin)]
)
async def logout(
    request: Request,
    response: Response,
    session: SessionDep,
    ww_refresh: Annotated[str | None, Cookie()] = None,
) -> Response:
    if ww_refresh:
        token = (
            await session.execute(
                select(RefreshToken).where(
                    RefreshToken.token_hash == hash_refresh_token(ww_refresh)
                )
            )
        ).scalar_one_or_none()
        if token and token.revoked_at is None:
            token.revoked_at = utcnow()
            await session.commit()
    response.status_code = status.HTTP_204_NO_CONTENT
    _clear_refresh_cookie(response)
    return response


@router.get("/me", response_model=AdminUserOut)
async def me(user: CurrentUser) -> AdminUserOut:
    return _user_out(user)
