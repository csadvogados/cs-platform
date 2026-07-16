from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = 'CS Platform'
    app_version: str = '4.1.1-admin-recovery'
    environment: str = 'development'
    database_url: str = 'sqlite:///./cs_platform.db'
    secret_key: str = 'CHANGE-ME-IN-PRODUCTION'
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    max_failed_login_attempts: int = 5
    login_lock_minutes: int = 15
    initial_admin_email: str = 'admin@csrecupera.com.br'
    initial_admin_password: str = 'ChangeMe123!'
    initial_organization_name: str = 'CS Advogados'
    admin_recovery_enabled: bool = False
    admin_recovery_key: str = ''
    cors_origins: str = 'http://localhost:3000,http://localhost:5173,https://sistema.rdsconsultoria.com.br'
    minimum_existential_reference: float = 600.0
    model_config = SettingsConfigDict(env_file='.env', extra='ignore', case_sensitive=False)
    @property
    def cors_origin_list(self) -> list[str]:
        return [v.strip() for v in self.cors_origins.split(',') if v.strip()]

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
