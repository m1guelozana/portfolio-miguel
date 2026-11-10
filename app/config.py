from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = f"sqlite:///{ROOT / 'portfolio.db'}"
    secret_key: str = "dev-only-change-me"

    admin_user: str = "admin"
    admin_password_hash: str = ""
    # True em produção (HTTPS), para o cookie de sessão só trafegar criptografado
    session_https_only: bool = False

    # Produção na Vercel: admin desligado e banco aberto somente para leitura
    admin_enabled: bool = True
    read_only: bool = False


settings = Settings()
