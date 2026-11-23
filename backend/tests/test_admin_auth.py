import httpx
import jwt
import pytest

from app.core.config import get_settings
from tests.conftest import ADMIN_EMAIL, EDITOR_EMAIL, PASSWORD, login

LOGIN = "/api/v1/admin/auth/login"
REFRESH = "/api/v1/admin/auth/refresh"
LOGOUT = "/api/v1/admin/auth/logout"
ME = "/api/v1/admin/auth/me"


async def test_login_sets_httponly_strict_cookie_and_returns_token(
    client: httpx.AsyncClient,
) -> None:
    resp = await client.post(LOGIN, json={"email": ADMIN_EMAIL.upper(), "password": PASSWORD})
    assert resp.status_code == 200
    body = resp.json()
    assert body["user"]["roles"] == ["admin"]
    assert body["expires_in"] == 15 * 60
    cookie = resp.headers["set-cookie"]
    assert "ww_refresh=" in cookie
    assert "HttpOnly" in cookie and "SameSite=strict" in cookie
    assert "Path=/api/v1/admin/auth" in cookie
    assert resp.headers["cache-control"] == "no-store"

    me = await client.get(ME, headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me.json()["email"] == ADMIN_EMAIL


async def test_wrong_password_and_unknown_user_same_response(client: httpx.AsyncClient) -> None:
    bad = {"password": "incorrecta-123456"}  # gitleaks:allow (contraseña falsa de prueba)
    wrong = await client.post(LOGIN, json={"email": ADMIN_EMAIL, **bad})
    unknown = await client.post(LOGIN, json={"email": "nadie@x.cl", **bad})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json()["title"] == unknown.json()["title"]


async def test_lockout_after_repeated_failures(client: httpx.AsyncClient) -> None:
    from app.cli import create_admin

    email = "bloqueo@example.com"
    await create_admin(email, "Bloqueo", "editor", PASSWORD)
    for _ in range(5):
        r = await client.post(LOGIN, json={"email": email, "password": "mala-contraseña-1"})
        assert r.status_code == 401
    # Bloqueada: ni siquiera la contraseña correcta funciona.
    r = await client.post(LOGIN, json={"email": email, "password": PASSWORD})
    assert r.status_code == 401


async def test_login_rate_limited_per_ip(client: httpx.AsyncClient) -> None:
    for _ in range(10):
        await client.post(LOGIN, json={"email": "x@x.cl", "password": "y"})
    r = await client.post(LOGIN, json={"email": "x@x.cl", "password": "y"})
    assert r.status_code == 429


@pytest.mark.parametrize(
    "token",
    [
        "no-es-un-jwt",
        jwt.encode({"sub": "x", "type": "access"}, "otra-clave", algorithm="HS256"),
        # "alg: none" no se acepta nunca.
        jwt.encode({"sub": "x", "type": "access"}, None, algorithm="none"),
    ],
)
async def test_invalid_tokens_rejected(client: httpx.AsyncClient, token: str) -> None:
    r = await client.get(ME, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


async def test_refresh_token_cannot_be_used_as_access(client: httpx.AsyncClient) -> None:
    settings = get_settings()
    forged = jwt.encode(
        {
            "sub": "x",
            "type": "refresh",
            "aud": "willwebs-admin",
            "iss": "willwebs",
            "iat": 0,
            "exp": 9999999999,
        },
        settings.jwt_secret.get_secret_value(),
        algorithm="HS256",
    )
    assert (await client.get(ME, headers={"Authorization": f"Bearer {forged}"})).status_code == 401


async def test_refresh_rotates_and_detects_reuse(client: httpx.AsyncClient) -> None:
    await client.post(LOGIN, json={"email": ADMIN_EMAIL, "password": PASSWORD})
    first = client.cookies.get("ww_refresh", path="/api/v1/admin/auth")
    assert first

    r1 = await client.post(REFRESH)
    assert r1.status_code == 200
    second = client.cookies.get("ww_refresh", path="/api/v1/admin/auth")
    assert second and second != first

    # Reutilizar el token viejo (robado) revoca toda la familia...
    client.cookies.set("ww_refresh", first, path="/api/v1/admin/auth")
    assert (await client.post(REFRESH)).status_code == 401
    # ...incluido el token vigente.
    client.cookies.set("ww_refresh", second, path="/api/v1/admin/auth")
    assert (await client.post(REFRESH)).status_code == 401


async def test_refresh_rejects_cross_origin(client: httpx.AsyncClient) -> None:
    await client.post(LOGIN, json={"email": ADMIN_EMAIL, "password": PASSWORD})
    r = await client.post(REFRESH, headers={"Origin": "https://evil.example"})
    assert r.status_code == 403


async def test_logout_revokes_refresh(client: httpx.AsyncClient) -> None:
    await client.post(LOGIN, json={"email": ADMIN_EMAIL, "password": PASSWORD})
    token = client.cookies.get("ww_refresh", path="/api/v1/admin/auth")
    assert (await client.post(LOGOUT)).status_code == 204
    client.cookies.set("ww_refresh", token, path="/api/v1/admin/auth")
    assert (await client.post(REFRESH)).status_code == 401


async def test_admin_endpoints_require_auth_and_roles(client: httpx.AsyncClient) -> None:
    assert (await client.get("/api/v1/admin/leads")).status_code == 401
    editor = await login(client, EDITOR_EMAIL)
    assert (await client.get("/api/v1/admin/leads", headers=editor)).status_code == 200
    # Solo admin: auditoría, legal y derechos del titular.
    assert (await client.get("/api/v1/admin/audit", headers=editor)).status_code == 403
    assert (await client.get("/api/v1/admin/legal", headers=editor)).status_code == 403
    r = await client.post(
        "/api/v1/admin/data-subject/export", headers=editor, json={"email": "a@b.cl"}
    )
    assert r.status_code == 403
