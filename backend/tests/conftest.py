"""Fixtures de integración contra MySQL real (base `<DB_NAME>_test`).

Se ejecutan en el contenedor `migrate` (tiene las credenciales del usuario migrator):
    docker compose -f docker-compose.yml -f docker-compose.dev.yml run --rm migrate pytest
Los tests que no usan la fixture `db` (p. ej. test_health) no requieren MySQL.
"""

import asyncio
import os
from collections.abc import AsyncIterator, Iterator

import httpx
import pytest

_BASE_DB = os.environ.get("DB_NAME", "willwebs")
if not _BASE_DB.endswith("_test"):
    os.environ["DB_NAME"] = f"{_BASE_DB}_test"
os.environ["APP_ENV"] = "test"
os.environ.setdefault("TURNSTILE_SECRET_KEY", "")
# En tests la app usa el usuario migrator sobre la base de tests.
if os.environ.get("MIGRATOR_DB_PASSWORD"):
    os.environ["APP_DB_USER"] = os.environ.get("MIGRATOR_DB_USER", "willwebs_migrator")
    os.environ["APP_DB_PASSWORD"] = os.environ["MIGRATOR_DB_PASSWORD"]

from app.core.config import get_settings  # noqa: E402

get_settings.cache_clear()

from app.core.ratelimit import limiter  # noqa: E402
from app.db.session import dispose_engine  # noqa: E402


@pytest.fixture(scope="session")
def db() -> Iterator[None]:
    """Recrea el esquema con las migraciones reales y carga los seeds."""
    if not os.environ.get("MIGRATOR_DB_PASSWORD"):
        pytest.skip("sin credenciales de MySQL (ejecutar en el contenedor migrate)")
    from alembic import command
    from alembic.config import Config

    from app import seeds

    cfg = Config(os.path.join(os.path.dirname(__file__), "..", "alembic.ini"))
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")
    asyncio.run(seeds.main())
    yield


@pytest.fixture(autouse=True)
async def _isolation() -> AsyncIterator[None]:
    limiter.reset()
    yield
    # Cada test tiene su propio event loop: no reutilizar conexiones entre loops.
    await dispose_engine()


@pytest.fixture
async def client(db: None) -> AsyncIterator[httpx.AsyncClient]:
    from app.main import create_app

    transport = httpx.ASGITransport(app=create_app(get_settings()), client=("203.0.113.7", 1234))
    async with httpx.AsyncClient(transport=transport, base_url="http://localhost") as c:
        yield c
