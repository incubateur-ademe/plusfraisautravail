from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    vigilance_app_id: str = Field(..., description="Météo-France API application ID for Vigilance.")

    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://localhost:4173",
            "https://plusfraisautravail.beta.gouv.fr",
        ],
        description="Origins allowed to call the API.",
    )

    cache_ttl_seconds: int = Field(default=3600, description="TTL for upstream-data cache.")


settings = Settings()  # type: ignore[call-arg]
