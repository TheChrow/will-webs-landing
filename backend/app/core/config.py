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

    allowed_hosts: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["localhost", "127.0.0.1"]
    )
    cors_origins: Annotated[list[str], NoDecode] = Field(default_factory=list)

    @field_validator("allowed_hosts", "cors_origins", mode="before")
    @classmethod
    def _parse_csv(cls, value: str | list[str]) -> list[str]:
        return _split_csv(value)

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
