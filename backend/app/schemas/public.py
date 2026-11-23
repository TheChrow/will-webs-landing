from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models import LegalDocumentType


class _Out(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class CategoryOut(_Out):
    slug: str
    name: str


class ServiceOut(_Out):
    id: str = Field(validation_alias="public_id")
    slug: str
    title: str
    summary: str
    description: str | None
    icon: str | None
    category: CategoryOut | None


class BannerOut(_Out):
    id: str = Field(validation_alias="public_id")
    title: str
    subtitle: str | None
    image_url: str | None
    image_alt: str
    cta_label: str | None
    cta_href: str | None


class ClientOut(_Out):
    id: str = Field(validation_alias="public_id")
    name: str
    logo_url: str | None
    logo_alt: str
    website_url: str | None


class ContentBlockOut(_Out):
    key: str
    locale: str
    title: str | None
    body: str


class LegalDocumentOut(BaseModel):
    type: LegalDocumentType
    slug: str
    title: str
    version: str
    body: str
    published_at: datetime | None
