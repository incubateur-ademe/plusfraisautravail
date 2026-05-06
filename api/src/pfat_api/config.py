from pydantic import Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class ConfigError(RuntimeError):
    """Raised when required configuration is missing or invalid."""


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    vigilance_app_id: str = Field(..., description="Météo-France API application ID for Vigilance.")

    rte_client_id: str | None = Field(
        default=None, description="RTE Data API OAuth client_id for Ecowatt."
    )
    rte_client_secret: str | None = Field(
        default=None, description="RTE Data API OAuth client_secret for Ecowatt."
    )
    rte_use_sandbox: bool = Field(
        default=False,
        description="Use the RTE sandbox endpoint (canned data, no rate limit) instead of prod.",
    )

    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://localhost:4173",
            "https://plusfraisautravail.beta.gouv.fr",
        ],
        description="Origins allowed to call the API.",
    )

    cache_ttl_seconds: int = Field(default=3600, description="TTL for upstream-data cache.")


def _load_settings() -> Settings:
    try:
        return Settings()  # type: ignore[call-arg]
    except ValidationError as exc:
        missing = [
            ".".join(str(loc) for loc in err["loc"])
            for err in exc.errors()
            if err["type"] == "missing"
        ]
        if missing:
            env_names = ", ".join(name.upper() for name in missing)
            raise ConfigError(
                f"Missing required configuration: {env_names}. "
                "Copy api/.env.example to api/.env and fill it in, "
                "or export the variables in your shell before starting the API."
            ) from exc
        raise


settings = _load_settings()
