"""Base settings schema with common GCP and environment parameters."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class AegisBaseSettings(BaseSettings):
    """Core settings shared across Aegis microservices."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    gcp_project: str = "aegis-fraud-ops-dev"
    aegis_env: str = "local"
    aegis_adapter_mode: str = "mock"  # mock | gcp
    aegis_log_level: str = "INFO"
    gemini_api_key: str | None = None
    google_maps_api_key: str | None = None

    @property
    def is_mock_mode(self) -> bool:
        """Return True if running offline with mock adapters."""
        return self.aegis_adapter_mode.lower() == "mock"
