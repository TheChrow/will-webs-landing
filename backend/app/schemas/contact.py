import re
from typing import Annotated, Literal

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    StringConstraints,
)

_SINGLE_LINE = re.compile(r"^[^\r\n\x00-\x1f\x7f]*$")
_CONTROL_EXCEPT_NEWLINES = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def _single_line(value: str) -> str:
    if not _SINGLE_LINE.match(value):
        raise ValueError("no se permiten saltos de línea ni caracteres de control")
    return value


def _clean_multiline(value: str) -> str:
    if _CONTROL_EXCEPT_NEWLINES.search(value):
        raise ValueError("no se permiten caracteres de control")
    return value


def _normalize_phone(value: str) -> str:
    digits = re.sub(r"[\s\-().]", "", value)
    if not re.fullmatch(r"\+?[0-9]{7,15}", digits):
        raise ValueError("teléfono inválido")
    return digits


def _lower(value: str) -> str:
    return value.lower()


SingleLine = Annotated[str, AfterValidator(_single_line)]


class ContactIn(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: Annotated[SingleLine, StringConstraints(min_length=2, max_length=120)]
    email: Annotated[EmailStr, Field(max_length=254), AfterValidator(_lower)]
    company: Annotated[SingleLine, StringConstraints(max_length=160)] | None = None
    phone: (
        Annotated[str, StringConstraints(max_length=32), AfterValidator(_normalize_phone)] | None
    ) = None
    service: (
        Annotated[str, StringConstraints(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$", max_length=120)]
        | None
    ) = None
    message: Annotated[
        str, StringConstraints(min_length=10, max_length=5000), AfterValidator(_clean_multiline)
    ]
    privacy_accepted: Literal[True] = Field(
        description="Debe ser true: aceptación de la Política de Privacidad vigente."
    )
    marketing_opt_in: bool = False

    # Anti-bot
    website: Annotated[str, StringConstraints(max_length=200)] = Field(
        default="", description="Honeypot: debe llegar vacío."
    )
    elapsed_ms: Annotated[int, Field(ge=0, le=86_400_000)] = Field(
        description="Milisegundos entre que se mostró el formulario y el envío."
    )
    captcha_token: Annotated[str, StringConstraints(max_length=2048)] | None = None


class ContactAccepted(BaseModel):
    status: Literal["accepted"] = "accepted"
