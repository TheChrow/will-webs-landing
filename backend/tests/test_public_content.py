import httpx


async def test_services_returns_seeded_catalog_in_order(client: httpx.AsyncClient) -> None:
    resp = await client.get("/api/v1/services")
    assert resp.status_code == 200
    assert resp.headers["cache-control"] == "public, max-age=300"
    services = resp.json()
    assert len(services) == 10
    assert services[0]["title"] == "Automatización de procesos"
    assert services[-1]["title"] == "Soporte continuo"
    assert len(services[0]["id"]) == 26  # ULID, nunca el id interno
    assert services[0]["category"]["slug"] == "automatizacion-ia"


async def test_service_detail_and_404(client: httpx.AsyncClient) -> None:
    ok = await client.get("/api/v1/services/software-a-medida")
    assert ok.status_code == 200 and ok.json()["slug"] == "software-a-medida"
    missing = await client.get("/api/v1/services/no-existe")
    assert missing.status_code == 404
    assert missing.headers["content-type"].startswith("application/problem+json")


async def test_service_slug_rejects_injection(client: httpx.AsyncClient) -> None:
    resp = await client.get("/api/v1/services/x' OR '1'='1")
    assert resp.status_code == 422


async def test_unpublished_content_is_hidden(client: httpx.AsyncClient) -> None:
    # Banners y misión/visión se siembran sin publicar (los tests del admin pueden publicar
    # otros registros en la base compartida, por eso se comprueban los sembrados).
    titles = {b["title"] for b in (await client.get("/api/v1/banners")).json()}
    assert not titles & {"Banner 1", "Banner 2", "Banner 3"}
    assert (await client.get("/api/v1/content/about.vision")).status_code == 404


async def test_content_by_prefix_escapes_wildcards(client: httpx.AsyncClient) -> None:
    hero = (await client.get("/api/v1/content", params={"prefix": "hero."})).json()
    assert {b["key"] for b in hero} == {"hero.title", "hero.lead"}
    # "_" es comodín en LIKE; debe tratarse literal.
    assert (await client.get("/api/v1/content", params={"prefix": "hero_"})).json() == []


async def test_legal_privacy_current_and_drafts_hidden(client: httpx.AsyncClient) -> None:
    privacy = await client.get("/api/v1/legal/privacy")
    assert privacy.status_code == 200
    assert privacy.json()["version"] == "0.1.0"
    assert (await client.get("/api/v1/legal/cookies")).status_code == 404
    assert (await client.get("/api/v1/legal/otro")).status_code == 422


async def test_public_settings_only(client: httpx.AsyncClient) -> None:
    settings = (await client.get("/api/v1/settings")).json()
    assert settings["company.name"] == "Will-Webs"


async def test_readiness_with_db(client: httpx.AsyncClient) -> None:
    resp = await client.get("/api/v1/health/ready")
    assert resp.json() == {"status": "ok", "database": "up"}
