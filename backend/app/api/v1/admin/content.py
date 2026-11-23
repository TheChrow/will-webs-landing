"""CRUD de master data: servicios, banners, empresas, bloques de contenido y ajustes.

Toda escritura queda en el audit log. Roles: admin y editor.
"""

from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, Path, Query, Request, Response, status
from pydantic import BaseModel, ValidationError
from sqlalchemy import func, inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.api.v1.admin.deps import AnyStaff, SessionDep, client_ip
from app.core.timeutil import utcnow
from app.db.base import Base
from app.models import (
    Banner,
    ClientCompany,
    ContactMessage,
    ContactStatus,
    ContentBlock,
    Service,
    ServiceCategory,
    SiteSetting,
)
from app.schemas.admin import (
    BannerAdminOut,
    BannerIn,
    BannerPatch,
    ClientAdminOut,
    ClientIn,
    ClientPatch,
    ContentBlockAdminOut,
    ContentBlockPut,
    ServiceAdminOut,
    ServiceIn,
    ServicePatch,
    SettingAdminOut,
    SettingPut,
)
from app.services import audit

router = APIRouter(tags=["admin-content"])

PublicId = Annotated[str, Path(pattern=r"^[0-9A-HJKMNP-TV-Z]{26}$")]
ContentKey = Annotated[str, Path(pattern=r"^[a-z0-9]+(\.[a-z0-9_]+)+$", max_length=100)]
SettingKey = Annotated[str, Path(pattern=r"^[a-z0-9]+(\.[a-z0-9_]+)+$", max_length=100)]
Locale = Annotated[str, Query(pattern=r"^[a-z]{2}(-[A-Z]{2})?$")]


def _apply(obj: Base, values: dict[str, Any]) -> dict[str, Any]:
    """Aplica cambios (rechaza null en columnas NOT NULL). Devuelve {campo: [antes, después]}."""
    mapper = inspect(type(obj))
    diff: dict[str, Any] = {}
    for key, new in values.items():
        column = mapper.columns.get(key)
        if column is not None and new is None and not column.nullable:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, f"'{key}' no puede ser null")
        old = getattr(obj, key)
        if old != new:
            diff[key] = [old, new]
            setattr(obj, key, new)
    return diff


async def _commit(session: SessionDep) -> None:
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Conflicto: valor duplicado o inválido"
        ) from None


# ======================= Servicios =======================


async def _category_id(session: SessionDep, slug: str | None) -> int | None:
    if slug is None:
        return None
    cat_id = (
        await session.execute(select(ServiceCategory.id).where(ServiceCategory.slug == slug))
    ).scalar_one_or_none()
    if cat_id is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Categoría desconocida")
    return cat_id


async def _get_service(session: SessionDep, public_id: str) -> Service:
    svc = (
        await session.execute(
            select(Service)
            .options(selectinload(Service.category))
            .where(Service.public_id == public_id, Service.deleted_at.is_(None))
        )
    ).scalar_one_or_none()
    if svc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Servicio no encontrado")
    return svc


def _service_out(s: Service) -> ServiceAdminOut:
    return ServiceAdminOut(
        id=s.public_id,
        slug=s.slug,
        title=s.title,
        summary=s.summary,
        description=s.description,
        icon=s.icon,
        category=s.category.slug if s.category else None,
        sort_order=s.sort_order,
        is_published=s.is_published,
        updated_at=s.updated_at,
    )


@router.get("/services", response_model=list[ServiceAdminOut])
async def list_services(_: AnyStaff, session: SessionDep) -> list[ServiceAdminOut]:
    rows = (
        await session.execute(
            select(Service)
            .options(selectinload(Service.category))
            .where(Service.deleted_at.is_(None))
            .order_by(Service.sort_order, Service.id)
        )
    ).scalars()
    return [_service_out(s) for s in rows]


@router.post("/services", response_model=ServiceAdminOut, status_code=status.HTTP_201_CREATED)
async def create_service(
    data: ServiceIn, user: AnyStaff, session: SessionDep, request: Request
) -> ServiceAdminOut:
    values = data.model_dump(exclude={"category"})
    svc = Service(
        **values,
        category_id=await _category_id(session, data.category),
        created_by=user.id,
        updated_by=user.id,
    )
    session.add(svc)
    await session.flush()
    audit.record(
        session,
        actor=user,
        action="create",
        entity="service",
        entity_id=svc.public_id,
        diff=data.model_dump(),
        ip=client_ip(request),
    )
    await _commit(session)
    return _service_out(await _get_service(session, svc.public_id))


@router.patch("/services/{public_id}", response_model=ServiceAdminOut)
async def update_service(
    public_id: PublicId, data: ServicePatch, user: AnyStaff, session: SessionDep, request: Request
) -> ServiceAdminOut:
    svc = await _get_service(session, public_id)
    values = data.model_dump(exclude_unset=True)
    if "category" in values:
        values["category_id"] = await _category_id(session, values.pop("category"))
    diff = _apply(svc, values)
    if diff:
        svc.updated_by = user.id
        audit.record(
            session,
            actor=user,
            action="update",
            entity="service",
            entity_id=public_id,
            diff=diff,
            ip=client_ip(request),
        )
        await _commit(session)
        session.expire_all()
    return _service_out(await _get_service(session, public_id))


@router.delete("/services/{public_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service(
    public_id: PublicId, user: AnyStaff, session: SessionDep, request: Request
) -> Response:
    svc = await _get_service(session, public_id)
    svc.deleted_at = utcnow()
    svc.is_published = False
    svc.updated_by = user.id
    audit.record(
        session,
        actor=user,
        action="delete",
        entity="service",
        entity_id=public_id,
        ip=client_ip(request),
    )
    await _commit(session)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ============ Banners y empresas (CRUD simétrico) ============


def _simple_crud(
    path: str,
    entity: str,
    model: type[Banner] | type[ClientCompany],
    in_schema: type[BaseModel],
    patch_schema: type[BaseModel],
    out_schema: type[BaseModel],
) -> None:
    async def get_obj(session: SessionDep, public_id: str) -> Any:
        obj = (
            await session.execute(
                select(model).where(model.public_id == public_id, model.deleted_at.is_(None))
            )
        ).scalar_one_or_none()
        if obj is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "No encontrado")
        return obj

    async def list_items(_: AnyStaff, session: SessionDep) -> list[Any]:
        rows = (
            await session.execute(
                select(model).where(model.deleted_at.is_(None)).order_by(model.sort_order, model.id)
            )
        ).scalars()
        return [out_schema.model_validate(r) for r in rows]

    async def create_item(
        data: in_schema,
        user: AnyStaff,
        session: SessionDep,  # type: ignore[valid-type]
        request: Request,
    ) -> Any:
        values = data.model_dump()  # type: ignore[attr-defined]
        obj = model(**values, created_by=user.id, updated_by=user.id)
        session.add(obj)
        await session.flush()
        audit.record(
            session,
            actor=user,
            action="create",
            entity=entity,
            entity_id=obj.public_id,
            diff=data.model_dump(),
            ip=client_ip(request),
        )  # type: ignore[attr-defined]
        await _commit(session)
        await session.refresh(obj)
        return out_schema.model_validate(obj)

    async def update_item(
        public_id: PublicId,
        data: patch_schema,
        user: AnyStaff,  # type: ignore[valid-type]
        session: SessionDep,
        request: Request,
    ) -> Any:
        obj = await get_obj(session, public_id)
        values = data.model_dump(exclude_unset=True)  # type: ignore[attr-defined]
        merged = {**{k: getattr(obj, k) for k in in_schema.model_fields}, **values}
        try:
            in_schema.model_validate(merged)  # revalidar reglas cruzadas (CTA, vigencia)
        except ValidationError as exc:
            msgs = "; ".join(e["msg"] for e in exc.errors())
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, msgs) from None
        diff = _apply(obj, values)
        if diff:
            obj.updated_by = user.id
            audit.record(
                session,
                actor=user,
                action="update",
                entity=entity,
                entity_id=public_id,
                diff=diff,
                ip=client_ip(request),
            )
            await _commit(session)
            await session.refresh(obj)
        return out_schema.model_validate(obj)

    async def delete_item(
        public_id: PublicId, user: AnyStaff, session: SessionDep, request: Request
    ) -> Response:
        obj = await get_obj(session, public_id)
        obj.deleted_at = utcnow()
        obj.is_published = False
        obj.updated_by = user.id
        audit.record(
            session,
            actor=user,
            action="delete",
            entity=entity,
            entity_id=public_id,
            ip=client_ip(request),
        )
        await _commit(session)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    router.add_api_route(f"/{path}", list_items, methods=["GET"], response_model=list[out_schema])
    router.add_api_route(
        f"/{path}",
        create_item,
        methods=["POST"],
        response_model=out_schema,
        status_code=status.HTTP_201_CREATED,
    )
    router.add_api_route(
        f"/{path}/{{public_id}}", update_item, methods=["PATCH"], response_model=out_schema
    )
    router.add_api_route(
        f"/{path}/{{public_id}}",
        delete_item,
        methods=["DELETE"],
        status_code=status.HTTP_204_NO_CONTENT,
    )


_simple_crud("banners", "banner", Banner, BannerIn, BannerPatch, BannerAdminOut)
_simple_crud("clients", "client_company", ClientCompany, ClientIn, ClientPatch, ClientAdminOut)


# ======================= Contenido =======================


@router.get("/content", response_model=list[ContentBlockAdminOut])
async def list_content(_: AnyStaff, session: SessionDep) -> list[ContentBlockAdminOut]:
    rows = (
        await session.execute(select(ContentBlock).order_by(ContentBlock.key, ContentBlock.locale))
    ).scalars()
    return [ContentBlockAdminOut.model_validate(r) for r in rows]


@router.put("/content/{key}", response_model=ContentBlockAdminOut)
async def put_content(
    key: ContentKey,
    data: ContentBlockPut,
    user: AnyStaff,
    session: SessionDep,
    request: Request,
    locale: Locale = "es-CL",
) -> ContentBlockAdminOut:
    block = (
        await session.execute(
            select(ContentBlock).where(ContentBlock.key == key, ContentBlock.locale == locale)
        )
    ).scalar_one_or_none()
    if block is None:
        block = ContentBlock(key=key, locale=locale, created_by=user.id, **data.model_dump())
        session.add(block)
        diff: dict[str, Any] = data.model_dump()
        action = "create"
    else:
        diff = _apply(block, data.model_dump())
        action = "update"
    block.updated_by = user.id
    if diff:
        audit.record(
            session,
            actor=user,
            action=action,
            entity="content_block",
            entity_id=f"{key}:{locale}"[:26],
            diff=diff,
            ip=client_ip(request),
        )
    await _commit(session)
    await session.refresh(block)
    return ContentBlockAdminOut.model_validate(block)


# ======================= Ajustes =======================


@router.get("/settings", response_model=list[SettingAdminOut])
async def list_settings(_: AnyStaff, session: SessionDep) -> list[SettingAdminOut]:
    rows = (await session.execute(select(SiteSetting).order_by(SiteSetting.key))).scalars()
    return [SettingAdminOut.model_validate(r) for r in rows]


@router.put("/settings/{key}", response_model=SettingAdminOut)
async def put_setting(
    key: SettingKey, data: SettingPut, user: AnyStaff, session: SessionDep, request: Request
) -> SettingAdminOut:
    setting = (
        await session.execute(select(SiteSetting).where(SiteSetting.key == key))
    ).scalar_one_or_none()
    if setting is None:
        setting = SiteSetting(key=key, created_by=user.id, **data.model_dump())
        session.add(setting)
        diff: dict[str, Any] = data.model_dump()
    else:
        diff = _apply(setting, data.model_dump())
    setting.updated_by = user.id
    if diff:
        audit.record(
            session,
            actor=user,
            action="upsert",
            entity="site_setting",
            entity_id=key[:26],
            diff=diff,
            ip=client_ip(request),
        )
    await _commit(session)
    await session.refresh(setting)
    return SettingAdminOut.model_validate(setting)


@router.get("/stats")
async def stats(_: AnyStaff, session: SessionDep) -> dict[str, int]:
    new_leads = (
        await session.execute(
            select(func.count())
            .select_from(ContactMessage)
            .where(ContactMessage.status == ContactStatus.new)
        )
    ).scalar_one()
    return {"new_leads": new_leads}
