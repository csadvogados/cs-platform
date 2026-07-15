from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "CS Platform"
    app_version: str = "2.0.0-integrated"
    environment: str = "development"
    database_url: str = "sqlite:///./cs_platform.db"
    secret_key: str = "CHANGE-ME-IN-PRODUCTION"
    access_token_expire_minutes: int = 60
    initial_admin_email: str = "admin@csrecupera.com.br"
    initial_admin_password: str = "ChangeMe123!"
    initial_organization_name: str = "CS Advogados"
    cors_origins: str = "http://localhost:3000,http://localhost:5173,https://sistema.rdsconsultoria.com.br"
    minimum_existential_reference: float = 600.0

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [x.strip() for x in self.cors_origins.split(',') if x.strip()]

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
