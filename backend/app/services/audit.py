from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.hashing import pseudonymize
from app.models import AdminUser, AuditLog


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [_jsonable(v) for v in value]
    if value is None or isinstance(value, bool | int | float | str):
        return value
    return str(value)


def record(
    session: AsyncSession,
    *,
    actor: AdminUser | None,
    action: str,
    entity: str,
    entity_id: str | None = None,
    diff: dict[str, Any] | None = None,
    ip: str | None = None,
) -> None:
    """Agrega una entrada append-only al audit log (se confirma con la transacción del caller)."""
    session.add(
        AuditLog(
            actor_id=actor.id if actor else None,
            action=action,
            entity=entity,
            entity_id=entity_id,
            diff=_jsonable(diff) if diff else None,
            ip_hash=pseudonymize(ip),
        )
    )
