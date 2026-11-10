from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./portfolio.db"
    secret_key: str = "dev-only-change-me"
    admin_user: str = "miguel"
    admin_password_hash: str = ""
    session_https_only: bool = False


settings = Settings()
