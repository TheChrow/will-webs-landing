import logging
import re
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.v1.health import router as health_router
from app.api.v1.public.contact import router as contact_router
from app.api.v1.public.content import router as content_router
from app.core.config import Settings, get_settings
from app.db.session import dispose_engine

logger = logging.getLogger("app")

_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9-]{1,64}$")


def _problem(
    status: int,
    title: str,
    detail: str | None = None,
    headers: dict[str, str] | None = None,
    **extra: object,
) -> JSONResponse:
    """Respuesta de error RFC 9457 (Problem Details)."""
    body: dict[str, object] = {"type": "about:blank", "title": title, "status": status}
    if detail:
        body["detail"] = detail
    body.update(extra)
    return JSONResponse(
        body, status_code=status, media_type="application/problem+json", headers=headers
    )


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    yield
    await dispose_engine()


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    logging.basicConfig(level=logging.INFO if settings.is_production else logging.DEBUG)

    app = FastAPI(
        title="Will-Webs API",
        version="0.1.0",
        lifespan=lifespan,
        # Swagger/OpenAPI solo fuera de producción.
        docs_url=None if settings.is_production else "/api/docs",
        redoc_url=None,
        openapi_url=None if settings.is_production else "/api/openapi.json",
    )

    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)
    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_methods=["GET", "POST", "PATCH", "DELETE"],
            allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
            allow_credentials=True,
        )

    @app.middleware("http")
    async def request_id(request: Request, call_next):  # type: ignore[no-untyped-def]
        incoming = request.headers.get("x-request-id", "")
        rid = incoming if _REQUEST_ID_RE.match(incoming) else uuid.uuid4().hex
        request.state.request_id = rid
        response = await call_next(request)
        response.headers["X-Request-ID"] = rid
        return response

    @app.exception_handler(StarletteHTTPException)
    async def http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        return _problem(exc.status_code, str(exc.detail), headers=getattr(exc, "headers", None))

    @app.exception_handler(RequestValidationError)
    async def validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        # Sin "input": no se devuelve el valor enviado (puede contener datos personales).
        errors = [{"loc": e["loc"], "msg": e["msg"], "type": e["type"]} for e in exc.errors()]
        return _problem(422, "Validation error", errors=errors)

    @app.exception_handler(Exception)
    async def unhandled_error(request: Request, _: Exception) -> JSONResponse:
        rid = getattr(request.state, "request_id", "-")
        logger.exception("error no controlado request_id=%s", rid)
        return _problem(500, "Internal Server Error")

    app.include_router(health_router, prefix="/api/v1")
    app.include_router(content_router, prefix="/api/v1")
    app.include_router(contact_router, prefix="/api/v1")
    return app


app = create_app()
