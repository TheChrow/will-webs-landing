"""Configuración por entorno (12-factor).

Los valores se leen de variables de entorno. Los secretos pueden venir de
Docker secrets: un archivo en /run/secrets/<nombre_del_campo> tiene prioridad
menor que la variable de entorno del mismo nombre.
"""

from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal
from urllib.parse import quote_plus

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

_SECRETS_DIR = Path("/run/secrets")


def _split_csv(value: str | list[str]) -> list[str]:
    if isinstance(value, list):
        return value
    return [item.strip() for item in value.split(",") if item.strip()]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=None,
        secrets_dir=_SECRETS_DIR if _SECRETS_DIR.is_dir() else None,
        extra="ignore",
    )

    app_env: Literal["development", "test", "production"] = "development"

    db_host: str = "db"
    db_port: int = 3306
    db_name: str = "willwebs"

    # Usuario de la aplicación: solo DML (SELECT/INSERT/UPDATE/DELETE).
    app_db_user: str = "willwebs_app"
    app_db_password: SecretStr = SecretStr("")

    # Usuario de migraciones: DDL sobre el schema. Solo lo usa Alembic.
    migrator_db_user: str = "willwebs_migrator"
    migrator_db_password: SecretStr = SecretStr("")

    # Pepper para seudonimizar IPs/emails (HMAC). Obligatorio en producción.
    hash_pepper: SecretStr = SecretStr("dev-only-pepper")

    # Cloudflare Turnstile. Vacío = verificación desactivada (solo fuera de producción).
    turnstile_secret_key: SecretStr = SecretStr("")
    turnstile_verify_url: str = "https://challenges.cloudflare.com/turnstile/v0/siteverify"

    # Correo de notificación de leads.
    smtp_host: str = "mailpit"
    smtp_port: int = 1025
    smtp_user: str = ""
    smtp_password: SecretStr = SecretStr("")
    smtp_starttls: bool = False
    mail_from: str = "Will-Webs <no-reply@localhost>"
    leads_notify_to: str = "leads@localhost"

    lead_retention_months: int = 24
    contact_min_fill_seconds: int = 3
    contact_rate_limit_per_hour: int = 5

    allowed_hosts: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["localhost", "127.0.0.1"]
    )
    cors_origins: Annotated[list[str], NoDecode] = Field(default_factory=list)

    @field_validator("allowed_hosts", "cors_origins", mode="before")
    @classmethod
    def _parse_csv(cls, value: str | list[str]) -> list[str]:
        return _split_csv(value)

    def model_post_init(self, __context: object) -> None:
        if self.is_production:
            missing = [
                name
                for name, value in (
                    ("hash_pepper", self.hash_pepper),
                    ("turnstile_secret_key", self.turnstile_secret_key),
                )
                if not value.get_secret_value() or value.get_secret_value() == "dev-only-pepper"
            ]
            if missing:
                raise ValueError(f"En producción faltan secretos: {', '.join(missing)}")

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    def _dsn(self, user: str, password: SecretStr) -> str:
        return (
            f"mysql+asyncmy://{quote_plus(user)}:{quote_plus(password.get_secret_value())}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}?charset=utf8mb4"
        )

    @property
    def app_database_url(self) -> str:
        return self._dsn(self.app_db_user, self.app_db_password)

    @property
    def migrator_database_url(self) -> str:
        return self._dsn(self.migrator_db_user, self.migrator_db_password)


@lru_cache
def get_settings() -> Settings:
    return Settings()
