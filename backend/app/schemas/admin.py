"""Esquemas del panel admin. Entradas estrictas (extra="forbid"); salidas sin IDs internos."""

import re
from datetime import date, datetime
from typing import Annotated, Any

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    StringConstraints,
    model_validator,
)

from app.models import ConsentPurpose, ContactStatus, LegalDocumentType

SLUG = r"^[a-z0-9]+(-[a-z0-9]+)*$"
CONTENT_KEY = r"^[a-z0-9]+(\.[a-z0-9_]+)+$"
SEMVER = r"^\d{1,3}\.\d{1,3}\.\d{1,3}$"


def _safe_href(value: str) -> str:
    # Solo anclas, rutas internas o https: nunca javascript:, data:, etc.
    if not re.match(r"^(#[\w-]*|/(?!/)[^\s]*|https://[^\s]+)$", value):
        raise ValueError("debe ser #ancla, /ruta o https://...")
    return value


def _https_url(value: str) -> str:
    if not re.match(r"^https://[^\s]+$", value):
        raise ValueError("debe comenzar con https://")
    return value


def _media_url(value: str) -> str:
    if not re.match(r"^(/(?!/)[^\s]*|https://[^\s]+)$", value):
        raise ValueError("debe ser /ruta o https://...")
    return value


Href = Annotated[str, StringConstraints(max_length=500), AfterValidator(_safe_href)]
HttpsUrl = Annotated[str, StringConstraints(max_length=500), AfterValidator(_https_url)]
MediaUrl = Annotated[str, StringConstraints(max_length=500), AfterValidator(_media_url)]
Slug = Annotated[str, StringConstraints(pattern=SLUG, max_length=120)]


class _In(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class _Out(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------- Auth ----------
class LoginIn(_In):
    email: Annotated[EmailStr, AfterValidator(str.lower)]
    password: Annotated[
        str, StringConstraints(min_length=1, max_length=256, strip_whitespace=False)
    ]


class AdminUserOut(BaseModel):
    id: str
    email: str
    full_name: str
    roles: list[str]


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"  # noqa: S105
    expires_in: int
    user: AdminUserOut


# ---------- Servicios ----------
class ServiceIn(_In):
    slug: Slug
    title: Annotated[str, StringConstraints(min_length=2, max_length=120)]
    summary: Annotated[str, StringConstraints(min_length=2, max_length=280)]
    description: Annotated[str, StringConstraints(max_length=20000)] | None = None
    icon: Annotated[str, StringConstraints(pattern=r"^[a-z0-9-]+$", max_length=64)] | None = None
    category: Slug | None = None
    sort_order: Annotated[int, Field(ge=0, le=32767)] = 0
    is_published: bool = False


class ServicePatch(_In):
    slug: Slug | None = None
    title: Annotated[str, StringConstraints(min_length=2, max_length=120)] | None = None
    summary: Annotated[str, StringConstraints(min_length=2, max_length=280)] | None = None
    description: Annotated[str, StringConstraints(max_length=20000)] | None = None
    icon: Annotated[str, StringConstraints(pattern=r"^[a-z0-9-]+$", max_length=64)] | None = None
    category: Slug | None = None
    sort_order: Annotated[int, Field(ge=0, le=32767)] | None = None
    is_published: bool | None = None


class ServiceAdminOut(BaseModel):
    id: str
    slug: str
    title: str
    summary: str
    description: str | None
    icon: str | None
    category: str | None
    sort_order: int
    is_published: bool
    updated_at: datetime


# ---------- Banners ----------
class BannerIn(_In):
    title: Annotated[str, StringConstraints(min_length=1, max_length=160)]
    subtitle: Annotated[str, StringConstraints(max_length=280)] | None = None
    image_url: MediaUrl | None = None
    image_alt: Annotated[str, StringConstraints(min_length=1, max_length=200)]
    cta_label: Annotated[str, StringConstraints(max_length=60)] | None = None
    cta_href: Href | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    sort_order: Annotated[int, Field(ge=0, le=32767)] = 0
    is_published: bool = False

    @model_validator(mode="after")
    def _check(self) -> "BannerIn":
        if self.cta_label and not self.cta_href:
            raise ValueError("cta_label requiere cta_href")
        if self.starts_at and self.ends_at and self.ends_at <= self.starts_at:
            raise ValueError("ends_at debe ser posterior a starts_at")
        return self


class BannerPatch(_In):
    title: Annotated[str, StringConstraints(min_length=1, max_length=160)] | None = None
    subtitle: Annotated[str, StringConstraints(max_length=280)] | None = None
    image_url: MediaUrl | None = None
    image_alt: Annotated[str, StringConstraints(min_length=1, max_length=200)] | None = None
    cta_label: Annotated[str, StringConstraints(max_length=60)] | None = None
    cta_href: Href | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    sort_order: Annotated[int, Field(ge=0, le=32767)] | None = None
    is_published: bool | None = None


class BannerAdminOut(_Out):
    id: str = Field(validation_alias="public_id")
    title: str
    subtitle: str | None
    image_url: str | None
    image_alt: str
    cta_label: str | None
    cta_href: str | None
    starts_at: datetime | None
    ends_at: datetime | None
    sort_order: int
    is_published: bool
    updated_at: datetime


# ---------- Empresas ----------
class ClientIn(_In):
    name: Annotated[str, StringConstraints(min_length=1, max_length=160)]
    logo_url: MediaUrl | None = None
    logo_alt: Annotated[str, StringConstraints(min_length=1, max_length=200)]
    website_url: HttpsUrl | None = None
    logo_consent_at: datetime | None = None
    sort_order: Annotated[int, Field(ge=0, le=32767)] = 0
    is_published: bool = False


class ClientPatch(_In):
    name: Annotated[str, StringConstraints(min_length=1, max_length=160)] | None = None
    logo_url: MediaUrl | None = None
    logo_alt: Annotated[str, StringConstraints(min_length=1, max_length=200)] | None = None
    website_url: HttpsUrl | None = None
    logo_consent_at: datetime | None = None
    sort_order: Annotated[int, Field(ge=0, le=32767)] | None = None
    is_published: bool | None = None


class ClientAdminOut(_Out):
    id: str = Field(validation_alias="public_id")
    name: str
    logo_url: str | None
    logo_alt: str
    website_url: str | None
    logo_consent_at: datetime | None
    sort_order: int
    is_published: bool
    updated_at: datetime


# ---------- Contenido y ajustes ----------
class ContentBlockPut(_In):
    title: Annotated[str, StringConstraints(max_length=200)] | None = None
    body: Annotated[str, StringConstraints(min_length=1, max_length=20000)]
    is_published: bool = False


class ContentBlockAdminOut(_Out):
    key: str
    locale: str
    title: str | None
    body: str
    is_published: bool
    updated_at: datetime


class SettingPut(_In):
    value: Annotated[str, StringConstraints(max_length=5000)]
    is_public: bool = False


class SettingAdminOut(_Out):
    key: str
    value: str
    is_public: bool
    updated_at: datetime


# ---------- Leads ----------
class LeadOut(BaseModel):
    id: str
    name: str
    email: str
    company: str | None
    phone: str | None
    service: str | None
    message: str | None
    status: ContactStatus
    created_at: datetime
    retention_until: date
    anonymized_at: datetime | None


class LeadPatch(_In):
    status: ContactStatus


class Page[T](BaseModel):
    items: list[T]
    total: int
    limit: int
    offset: int


class DataSubjectIn(_In):
    email: Annotated[EmailStr, AfterValidator(str.lower)]


class ConsentOut(BaseModel):
    purpose: ConsentPurpose
    granted: bool
    created_at: datetime
    document: LegalDocumentType
    version: str


class DataSubjectOut(BaseModel):
    email: str
    leads: list[LeadOut]
    consents: list[ConsentOut]


class AnonymizeOut(BaseModel):
    anonymized: int


# ---------- Legal ----------
class LegalVersionIn(_In):
    version: Annotated[str, StringConstraints(pattern=SEMVER)]
    body: Annotated[str, StringConstraints(min_length=1, max_length=200_000)]


class LegalBodyPatch(_In):
    body: Annotated[str, StringConstraints(min_length=1, max_length=200_000)]


class LegalVersionOut(BaseModel):
    version: str
    is_current: bool
    published_at: datetime | None
    created_at: datetime
    body: str | None = None


class LegalDocumentAdminOut(BaseModel):
    type: LegalDocumentType
    slug: str
    title: str
    versions: list[LegalVersionOut]


# ---------- Auditoría ----------
class AuditOut(BaseModel):
    action: str
    entity: str
    entity_id: str | None
    actor: str | None
    diff: dict[str, Any] | None
    created_at: datetime
