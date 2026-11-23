from datetime import date, timedelta

import httpx
from sqlalchemy import update

from app.db.session import get_engine
from app.models import ContactMessage
from tests.conftest import login

A = "/api/v1/admin"
VALID_LEAD = {
    "name": "Titular Datos",
    "email": "titular@example.com",
    "message": "Quiero información de sus servicios.",
    "privacy_accepted": True,
    "elapsed_ms": 8000,
}


async def test_service_crud_reflects_on_public_api_and_is_audited(
    client: httpx.AsyncClient,
) -> None:
    h = await login(client)
    created = await client.post(
        f"{A}/services",
        headers=h,
        json={
            "slug": "auditoria-ti",
            "title": "Auditoría TI",
            "summary": "Revisamos tu TI.",
            "category": "consultoria",
            "icon": "shield-check",
            "sort_order": 999,
        },
    )
    assert created.status_code == 201, created.text
    sid = created.json()["id"]
    # Borrador: no visible públicamente.
    assert (await client.get("/api/v1/services/auditoria-ti")).status_code == 404

    pub = await client.patch(f"{A}/services/{sid}", headers=h, json={"is_published": True})
    assert pub.json()["is_published"] is True
    assert (await client.get("/api/v1/services/auditoria-ti")).status_code == 200

    # null en columna obligatoria -> 422, no 500
    assert (
        await client.patch(f"{A}/services/{sid}", headers=h, json={"title": None})
    ).status_code == 422
    # slug duplicado -> 409
    dup = await client.patch(f"{A}/services/{sid}", headers=h, json={"slug": "integraciones"})
    assert dup.status_code == 409

    assert (await client.delete(f"{A}/services/{sid}", headers=h)).status_code == 204
    assert (await client.get("/api/v1/services/auditoria-ti")).status_code == 404

    log = (await client.get(f"{A}/audit", headers=h)).json()["items"]
    actions = [(e["action"], e["entity"]) for e in log if e["entity_id"] == sid]
    assert ("create", "service") in actions and ("delete", "service") in actions
    update_entry = next(e for e in log if e["entity_id"] == sid and e["action"] == "update")
    assert update_entry["diff"] == {"is_published": [False, True]}
    assert update_entry["actor"] == "admin@example.com"


async def test_banner_rejects_dangerous_links(client: httpx.AsyncClient) -> None:
    h = await login(client)
    for href in ("javascript:alert(1)", "data:text/html,x", "//evil.example"):
        r = await client.post(
            f"{A}/banners",
            headers=h,
            json={
                "title": "X",
                "image_alt": "x",
                "cta_label": "Ir",
                "cta_href": href,
            },
        )
        assert r.status_code == 422, href
    ok = await client.post(
        f"{A}/banners",
        headers=h,
        json={
            "title": "Promo",
            "image_alt": "Equipo trabajando",
            "cta_label": "Ir",
            "cta_href": "#contacto",
            "is_published": True,
        },
    )
    assert ok.status_code == 201
    # Regla cruzada al editar: quitar el href dejando el label -> 422
    bad = await client.patch(f"{A}/banners/{ok.json()['id']}", headers=h, json={"cta_href": None})
    assert bad.status_code == 422
    assert any(b["title"] == "Promo" for b in (await client.get("/api/v1/banners")).json())


async def test_client_logo_requires_consent_to_be_public(client: httpx.AsyncClient) -> None:
    h = await login(client)
    r = await client.post(
        f"{A}/clients",
        headers=h,
        json={
            "name": "ACME",
            "logo_alt": "Logo ACME",
            "is_published": True,
        },
    )
    cid = r.json()["id"]
    assert all(c["name"] != "ACME" for c in (await client.get("/api/v1/clients")).json())
    await client.patch(
        f"{A}/clients/{cid}", headers=h, json={"logo_consent_at": "2026-11-01T00:00:00"}
    )
    assert any(c["name"] == "ACME" for c in (await client.get("/api/v1/clients")).json())


async def test_content_block_upsert_publishes_mission(client: httpx.AsyncClient) -> None:
    h = await login(client)
    r = await client.put(
        f"{A}/content/about.mission",
        headers=h,
        json={
            "title": "Misión",
            "body": "Acompañar a las empresas.",
            "is_published": True,
        },
    )
    assert r.status_code == 200
    pub = await client.get("/api/v1/content/about.mission")
    assert pub.json()["body"] == "Acompañar a las empresas."


async def test_leads_inbox_and_status(client: httpx.AsyncClient) -> None:
    await client.post("/api/v1/contact", json=VALID_LEAD)
    h = await login(client)
    page = (await client.get(f"{A}/leads", headers=h, params={"status": "new"})).json()
    lead = next(i for i in page["items"] if i["email"] == "titular@example.com")
    r = await client.patch(f"{A}/leads/{lead['id']}", headers=h, json={"status": "contacted"})
    assert r.json()["status"] == "contacted"
    bad = await client.patch(f"{A}/leads/{lead['id']}", headers=h, json={"status": "borrado"})
    assert bad.status_code == 422


async def test_data_subject_export_and_anonymize(client: httpx.AsyncClient) -> None:
    email = "derechos@example.com"
    await client.post(
        "/api/v1/contact", json={**VALID_LEAD, "email": email, "marketing_opt_in": True}
    )
    h = await login(client)
    export = (
        await client.post(f"{A}/data-subject/export", headers=h, json={"email": email})
    ).json()
    assert len(export["leads"]) == 1
    assert {c["purpose"] for c in export["consents"]} == {"contact", "marketing"}
    assert export["consents"][0]["document"] == "privacy"

    anon = await client.post(f"{A}/data-subject/anonymize", headers=h, json={"email": email})
    assert anon.json() == {"anonymized": 1}
    again = (await client.post(f"{A}/data-subject/export", headers=h, json={"email": email})).json()
    assert again["leads"] == []  # ya no hay datos personales asociados al email
    assert len(again["consents"]) == 2  # la prueba del consentimiento se conserva


async def test_legal_versioning_and_immutability(client: httpx.AsyncClient) -> None:
    h = await login(client)
    r = await client.post(
        f"{A}/legal/terms/versions",
        headers=h,
        json={"version": "1.0.0", "body": "# Términos\n\nTexto."},
    )
    assert r.status_code == 201
    assert (await client.get("/api/v1/legal/terms")).status_code == 404  # borrador

    assert (
        await client.patch(
            f"{A}/legal/terms/versions/1.0.0",
            headers=h,
            json={"body": "# Términos\n\nTexto corregido."},
        )
    ).status_code == 200
    pub = await client.post(f"{A}/legal/terms/versions/1.0.0/publish", headers=h)
    assert pub.json()["is_current"] is True
    public = (await client.get("/api/v1/legal/terms")).json()
    assert public["version"] == "1.0.0" and "corregido" in public["body"]

    # Publicada => inmutable
    locked = await client.patch(
        f"{A}/legal/terms/versions/1.0.0", headers=h, json={"body": "cambio"}
    )
    assert locked.status_code == 409
    dup = await client.post(
        f"{A}/legal/terms/versions", headers=h, json={"version": "1.0.0", "body": "x"}
    )
    assert dup.status_code == 409


async def test_retention_job_anonymizes_expired_leads(client: httpx.AsyncClient) -> None:
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from app.jobs.retention import run_retention

    email = "vencido@example.com"
    await client.post("/api/v1/contact", json={**VALID_LEAD, "email": email})
    async with get_engine().begin() as conn:
        await conn.execute(
            update(ContactMessage)
            .where(ContactMessage.email == email)
            .values(retention_until=date.today() - timedelta(days=1))
        )
    async with async_sessionmaker(get_engine())() as session:
        result = await run_retention(session)
    assert result["leads_anonymized"] >= 1

    h = await login(client)
    export = (
        await client.post(f"{A}/data-subject/export", headers=h, json={"email": email})
    ).json()
    assert export["leads"] == []
