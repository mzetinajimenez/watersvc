"""Application configuration using pydantic-settings."""

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    mongodb_uri: str
    mongodb_database: str = "watersvc"
    default_timezone: str = "UTC"
    default_daily_goal_oz: float = 64.0
    max_intake_oz: float = 500.0

    # Auth
    jwt_secret: SecretStr
    jwt_expiry_hours: int = 168  # 7 days
    apple_bundle_id: str = "com.mzj.toma-aguita"
    google_client_id: str = ""

    @field_validator("jwt_secret")
    @classmethod
    def jwt_secret_must_be_set(cls, v: SecretStr) -> SecretStr:
        if len(v.get_secret_value()) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters")
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
