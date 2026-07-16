from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.constants import (
    APP_NAME,
    APP_VERSION,
    DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES,
    DEFAULT_DATABASE_MAX_OVERFLOW,
    DEFAULT_DATABASE_POOL_RECYCLE_SECONDS,
    DEFAULT_DATABASE_POOL_SIZE,
    DEFAULT_DATABASE_POOL_TIMEOUT_SECONDS,
    DEFAULT_ENVIRONMENT,
    DEFAULT_LOGIN_LOCK_MINUTES,
    DEFAULT_LOG_LEVEL,
    DEFAULT_MAX_FAILED_LOGIN_ATTEMPTS,
    DEFAULT_ORGANIZATION_NAME,
    DEFAULT_REFRESH_TOKEN_EXPIRE_DAYS,
    DEFAULT_TIMEZONE,
    JWT_ALGORITHM,
)


class Settings(BaseSettings):
    app_name: str = APP_NAME
    app_version: str = APP_VERSION
    environment: str = DEFAULT_ENVIRONMENT
    timezone: str = DEFAULT_TIMEZONE
    debug: bool = False

    api_v1_prefix: str = "/api/v1"
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
    openapi_url: str = "/openapi.json"

    database_url: str = "sqlite:///./cs_platform.db"
    database_pool_size: int = DEFAULT_DATABASE_POOL_SIZE
    database_max_overflow: int = DEFAULT_DATABASE_MAX_OVERFLOW
    database_pool_timeout_seconds: int = DEFAULT_DATABASE_POOL_TIMEOUT_SECONDS
    database_pool_recycle_seconds: int = DEFAULT_DATABASE_POOL_RECYCLE_SECONDS

    secret_key: str = "CHANGE-ME-IN-PRODUCTION"
    jwt_algorithm: str = JWT_ALGORITHM
    access_token_expire_minutes: int = DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES
    refresh_token_expire_days: int = DEFAULT_REFRESH_TOKEN_EXPIRE_DAYS
    max_failed_login_attempts: int = DEFAULT_MAX_FAILED_LOGIN_ATTEMPTS
    login_lock_minutes: int = DEFAULT_LOGIN_LOCK_MINUTES

    initial_admin_email: str = "admin@csrecupera.com.br"
    initial_admin_password: str = "ChangeMe123!"
    initial_organization_name: str = DEFAULT_ORGANIZATION_NAME

    reset_admin_on_startup: bool = False
    reset_admin_password: str = ""

    cors_origins: str = (
        "http://localhost:3000,"
        "http://localhost:5173,"
        "https://sistema.rdsconsultoria.com.br"
    )

    minimum_existential_reference: float = 600.0

    log_level: str = DEFAULT_LOG_LEVEL
    log_json: bool = False
    healthcheck_database: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=False,
    )

    @field_validator("environment", "log_level")
    @classmethod
    def normalize_text_values(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("SECRET_KEY não pode estar vazia.")
        return value.strip()

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("DATABASE_URL não pode estar vazia.")
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
