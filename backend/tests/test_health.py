import httpx
import pytest

from app.core.config import Settings
from app.main import create_app


def _client(settings: Settings) -> httpx.AsyncClient:
    transport = httpx.ASGITransport(app=create_app(settings))
    return httpx.AsyncClient(transport=transport, base_url="http://localhost")


@pytest.fixture
def dev_settings() -> Settings:
    return Settings(app_env="test", allowed_hosts=["localhost"])


async def test_liveness(dev_settings: Settings) -> None:
    async with _client(dev_settings) as client:
        resp = await client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
    assert resp.headers["x-request-id"]


async def test_request_id_is_sanitized(dev_settings: Settings) -> None:
    async with _client(dev_settings) as client:
        resp = await client.get("/api/v1/health", headers={"X-Request-ID": "bad\nvalue<script>"})
    assert resp.headers["x-request-id"] != "bad\nvalue<script>"


async def test_unknown_route_returns_problem_details(dev_settings: Settings) -> None:
    async with _client(dev_settings) as client:
        resp = await client.get("/api/v1/no-existe")
    assert resp.status_code == 404
    assert resp.headers["content-type"].startswith("application/problem+json")
    assert resp.json()["status"] == 404


async def test_untrusted_host_rejected(dev_settings: Settings) -> None:
    async with _client(dev_settings) as client:
        resp = await client.get("/api/v1/health", headers={"Host": "evil.example"})
    assert resp.status_code == 400


async def test_docs_disabled_in_production() -> None:
    settings = Settings(app_env="production", allowed_hosts=["localhost"])
    async with _client(settings) as client:
        assert (await client.get("/api/docs")).status_code == 404
        assert (await client.get("/api/openapi.json")).status_code == 404
