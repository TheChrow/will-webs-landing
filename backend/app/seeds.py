"""Seeds de master data (contenido actual de la landing).

Idempotente: solo inserta lo que falta (upsert por slug/key); nunca sobrescribe
contenido ya editado. Uso: ``python -m app.seeds`` (lo ejecuta el job ``migrate``).
"""

import asyncio
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.db.base import Base
from app.models import (
    Banner,
    ContentBlock,
    LegalDocument,
    LegalDocumentType,
    LegalDocumentVersion,
    Role,
    Service,
    ServiceCategory,
    SiteSetting,
)

logger = logging.getLogger("seeds")

CATEGORIES = [
    ("desarrollo", "Desarrollo de software", 10),
    ("automatizacion-ia", "Automatización e IA", 20),
    ("infraestructura", "Infraestructura y seguridad", 30),
    ("consultoria", "Consultoría y soporte", 40),
]

# (slug, título, resumen, categoría, ícono) — en el orden de la landing.
SERVICES = [
    (
        "automatizacion-de-procesos",
        "Automatización de procesos",
        "Automatizamos procesos empresariales.",
        "automatizacion-ia",
        "workflow",
    ),
    (
        "software-a-medida",
        "Software a medida",
        "Creamos software que se adapta a tu empresa.",
        "desarrollo",
        "code",
    ),
    ("integraciones", "Integraciones", "Integramos todas tus plataformas.", "desarrollo", "plug"),
    (
        "inteligencia-artificial",
        "Inteligencia Artificial",
        "Implementamos IA para aumentar la productividad.",
        "automatizacion-ia",
        "sparkles",
    ),
    (
        "infraestructura",
        "Infraestructura",
        "Modernizamos tu infraestructura tecnológica.",
        "infraestructura",
        "server",
    ),
    (
        "correo-empresarial",
        "Correo empresarial",
        "Migramos y administramos tu correo empresarial.",
        "infraestructura",
        "mail",
    ),
    (
        "aplicaciones-web",
        "Aplicaciones web",
        "Desarrollamos aplicaciones web escalables.",
        "desarrollo",
        "globe",
    ),
    (
        "respaldo-y-seguridad",
        "Respaldo y seguridad",
        "Protegemos y respaldamos tu información.",
        "infraestructura",
        "shield-check",
    ),
    (
        "transformacion-digital",
        "Transformación digital",
        "Acompañamos la transformación digital de tu empresa.",
        "consultoria",
        "trending-up",
    ),
    (
        "soporte-continuo",
        "Soporte continuo",
        "Brindamos soporte tecnológico continuo.",
        "consultoria",
        "life-buoy",
    ),
]

BANNERS = [
    ("Banner 1", "Imagen provisional del banner 1"),
    ("Banner 2", "Imagen provisional del banner 2"),
    ("Banner 3", "Imagen provisional del banner 3"),
]

# (key, título, cuerpo, publicado)
CONTENT = [
    ("hero.title", None, "Modernizamos tu empresa con software a medida", True),
    (
        "hero.lead",
        None,
        "Automatizamos procesos, integramos tus plataformas e implementamos inteligencia "
        "artificial para aumentar tu productividad.",
        True,
    ),
    ("cta.text", None, "¿Listo para dar el siguiente paso?", True),
    ("about.mission", "Misión", "Texto de misión pendiente de definir.", False),
    ("about.vision", "Visión", "Texto de visión pendiente de definir.", False),
]

SETTINGS = [
    ("company.name", "Will-Webs", True),
    ("contact.email", "contacto@example.com", True),
]

LEGAL = [
    (LegalDocumentType.privacy, "privacidad", "Política de Privacidad"),
    (LegalDocumentType.cookies, "cookies", "Política de Cookies"),
    (LegalDocumentType.terms, "terminos", "Términos y Condiciones"),
    (LegalDocumentType.accessibility, "accesibilidad", "Declaración de Accesibilidad"),
]
DRAFT_BODY = "> **Borrador provisional** — texto pendiente de revisión legal.\n"
# Borradores completos (app/legal/*.md) como versión 0.2.0 SIN publicar: un admin los
# revisa, completa los datos entre corchetes y publica desde el panel.
LEGAL_DRAFTS_DIR = Path(__file__).parent / "legal"
LEGAL_DRAFT_VERSION = "0.2.0"

ROLES = [("admin", "Acceso total"), ("editor", "Gestiona contenido y leads")]


async def _get_or_add(
    session: AsyncSession, model: type[Base], where: dict[str, Any], values: dict[str, Any]
) -> tuple[Any, bool]:
    stmt = select(model).filter_by(**where)
    obj = (await session.execute(stmt)).scalar_one_or_none()
    if obj is not None:
        return obj, False
    obj = model(**where, **values)
    session.add(obj)
    await session.flush()
    return obj, True


async def seed(session: AsyncSession) -> dict[str, int]:
    created: dict[str, int] = {}

    def count(name: str, was_created: bool) -> None:
        created[name] = created.get(name, 0) + int(was_created)

    categories: dict[str, ServiceCategory] = {}
    for slug, name, order in CATEGORIES:
        cat, new = await _get_or_add(
            session, ServiceCategory, {"slug": slug}, {"name": name, "sort_order": order}
        )
        categories[slug] = cat
        count("service_category", new)

    for i, (slug, title, summary, cat_slug, icon) in enumerate(SERVICES, start=1):
        _, new = await _get_or_add(
            session,
            Service,
            {"slug": slug},
            {
                "title": title,
                "summary": summary,
                "icon": icon,
                "sort_order": i * 10,
                "category_id": categories[cat_slug].id,
                "is_published": True,
            },
        )
        count("service", new)

    for i, (title, alt) in enumerate(BANNERS, start=1):
        _, new = await _get_or_add(
            session,
            Banner,
            {"title": title},
            {
                "image_alt": alt,
                "sort_order": i * 10,
                "is_published": False,
                "cta_label": "Contáctenos",
                "cta_href": "#contacto",
            },
        )
        count("banner", new)

    for key, title, body, published in CONTENT:
        _, new = await _get_or_add(
            session,
            ContentBlock,
            {"key": key, "locale": "es-CL"},
            {"title": title, "body": body, "is_published": published},
        )
        count("content_block", new)

    for key, value, public in SETTINGS:
        _, new = await _get_or_add(
            session, SiteSetting, {"key": key}, {"value": value, "is_public": public}
        )
        count("site_setting", new)

    now = datetime.now(UTC).replace(tzinfo=None)
    for doc_type, slug, title in LEGAL:
        doc, new = await _get_or_add(
            session, LegalDocument, {"type": doc_type}, {"slug": slug, "title": title}
        )
        count("legal_document", new)
        # La política de privacidad provisional queda vigente para que el formulario funcione.
        is_privacy = doc_type is LegalDocumentType.privacy
        _, new = await _get_or_add(
            session,
            LegalDocumentVersion,
            {"document_id": doc.id, "version": "0.1.0"},
            {
                "body": DRAFT_BODY,
                "is_current": is_privacy,
                "published_at": now if is_privacy else None,
            },
        )
        count("legal_document_version", new)

        draft_file = LEGAL_DRAFTS_DIR / f"{doc_type.value}.md"
        if draft_file.is_file():
            _, new = await _get_or_add(
                session,
                LegalDocumentVersion,
                {"document_id": doc.id, "version": LEGAL_DRAFT_VERSION},
                {"body": draft_file.read_text(encoding="utf-8"), "is_current": False},
            )
            count("legal_document_version", new)

    for name, description in ROLES:
        _, new = await _get_or_add(session, Role, {"name": name}, {"description": description})
        count("role", new)

    return created


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s [%(name)s] %(message)s")
    engine = create_async_engine(get_settings().migrator_database_url)
    async with async_sessionmaker(engine)() as session, session.begin():
        created = await seed(session)
    await engine.dispose()
    logger.info("seeds aplicados; registros nuevos: %s", created or "ninguno")


if __name__ == "__main__":
    asyncio.run(main())
