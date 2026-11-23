from datetime import date
from typing import Any

import httpx
import pytest
from sqlalchemy import func, select

from app.db.session import get_engine
from app.models import ConsentPurpose, ConsentRecord, ContactMessage
from app.services import captcha, mailer
from app.services.leads import add_months

VALID: dict[str, Any] = {
    "name": "Ana Pérez",
    "email": "Ana@Example.COM",
    "company": "ACME SpA",
    "phone": "+56 9 1234 5678",
    "service": "software-a-medida",
    "message": "Hola, necesitamos un sistema de inventario.",
    "privacy_accepted": True,
    "elapsed_ms": 8000,
}


@pytest.fixture
def sent(monkeypatch: pytest.MonkeyPatch) -> list[mailer.LeadNotification]:
    outbox: list[mailer.LeadNotification] = []
    monkeypatch.setattr(mailer, "send_lead_notification", outbox.append)
    return outbox


async def _count(model: type) -> int:
    async with get_engine().connect() as conn:
        return (await conn.execute(select(func.count()).select_from(model))).scalar_one()


async def _latest_lead() -> Any:
    async with get_engine().connect() as conn:
        return (
            await conn.execute(select(ContactMessage).order_by(ContactMessage.id.desc()).limit(1))
        ).one()


async def test_valid_submission_creates_lead_consent_and_email(
    client: httpx.AsyncClient, sent: list[mailer.LeadNotification]
) -> None:
    before = await _count(ContactMessage)
    resp = await client.post("/api/v1/contact", json={**VALID, "marketing_opt_in": True})
    assert resp.status_code == 202
    assert resp.json() == {"status": "accepted"}
    assert await _count(ContactMessage) == before + 1

    lead = await _latest_lead()
    assert lead.email == "ana@example.com"
    assert lead.phone == "+56912345678"
    assert lead.ip_hash is not None and b"203.0.113.7" not in lead.ip_hash
    assert lead.retention_until > date.today()

    async with get_engine().connect() as conn:
        purposes = (
            (
                await conn.execute(
                    select(ConsentRecord.purpose).where(
                        ConsentRecord.subject_email_hash
                        == select(ConsentRecord.subject_email_hash)
                        .where(ConsentRecord.id == lead.consent_record_id)
                        .scalar_subquery()
                    )
                )
            )
            .scalars()
            .all()
        )
    assert {ConsentPurpose.contact, ConsentPurpose.marketing} <= set(purposes)

    assert len(sent) == 1 and sent[0].service == "Software a medida"


async def test_privacy_must_be_accepted(client: httpx.AsyncClient, sent: list) -> None:
    resp = await client.post("/api/v1/contact", json={**VALID, "privacy_accepted": False})
    assert resp.status_code == 422
    assert sent == []


@pytest.mark.parametrize(
    "field,value",
    [
        ("name", "Ana\r\nBcc: victima@example.com"),  # inyección de cabeceras
        ("email", "no-es-un-email"),
        ("message", "corto"),
        ("message", "x" * 5001),
        ("phone", "abc"),
        ("service", "../../etc/passwd"),
    ],
)
async def test_invalid_fields_rejected(
    client: httpx.AsyncClient, sent: list, field: str, value: str
) -> None:
    resp = await client.post("/api/v1/contact", json={**VALID, field: value})
    assert resp.status_code == 422
    # El error no devuelve el valor enviado.
    assert value not in resp.text
    assert sent == []


async def test_unknown_fields_rejected(client: httpx.AsyncClient, sent: list) -> None:
    resp = await client.post("/api/v1/contact", json={**VALID, "status": "contacted"})
    assert resp.status_code == 422


async def test_unknown_service_rejected(client: httpx.AsyncClient, sent: list) -> None:
    resp = await client.post("/api/v1/contact", json={**VALID, "service": "no-existe"})
    assert resp.status_code == 422


async def test_sql_injection_payload_is_stored_as_plain_text(
    client: httpx.AsyncClient, sent: list
) -> None:
    payload = "Robert'); DROP TABLE contact_message;-- <script>alert(1)</script>"
    resp = await client.post("/api/v1/contact", json={**VALID, "message": payload})
    assert resp.status_code == 202
    assert (await _latest_lead()).message == payload  # guardado literal, tabla intacta


@pytest.mark.parametrize("override", [{"website": "http://spam.example"}, {"elapsed_ms": 500}])
async def test_bots_get_silent_accept_without_storing(
    client: httpx.AsyncClient, sent: list, override: dict
) -> None:
    before = await _count(ContactMessage)
    resp = await client.post("/api/v1/contact", json={**VALID, **override})
    assert resp.status_code == 202
    assert await _count(ContactMessage) == before
    assert sent == []


async def test_failed_captcha_rejected(
    client: httpx.AsyncClient, sent: list, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def fail(*_: object) -> bool:
        return False

    monkeypatch.setattr(captcha, "verify_captcha", fail)
    resp = await client.post("/api/v1/contact", json=VALID)
    assert resp.status_code == 400
    assert sent == []


async def test_rate_limit_per_ip(client: httpx.AsyncClient, sent: list) -> None:
    for i in range(5):
        r = await client.post("/api/v1/contact", json={**VALID, "email": f"user{i}@example.com"})
        assert r.status_code == 202
    blocked = await client.post("/api/v1/contact", json={**VALID, "email": "otro@example.com"})
    assert blocked.status_code == 429
    assert int(blocked.headers["retry-after"]) > 0


def test_add_months_end_of_month() -> None:
    assert add_months(date(2026, 1, 31), 1) == date(2026, 2, 28)
    assert add_months(date(2026, 11, 23), 24) == date(2028, 11, 23)
