import logging

from fastapi import APIRouter, Response, status
from sqlalchemy import text

from app.db.session import get_engine

router = APIRouter(tags=["health"])
logger = logging.getLogger(__name__)


@router.get("/health")
async def liveness() -> dict[str, str]:
    """El proceso está vivo (no toca dependencias)."""
    return {"status": "ok"}


@router.get("/health/ready")
async def readiness(response: Response) -> dict[str, str]:
    """La API puede atender tráfico: la base de datos responde."""
    try:
        async with get_engine().connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        logger.exception("readiness: base de datos no disponible")
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unavailable", "database": "down"}
    return {"status": "ok", "database": "up"}
