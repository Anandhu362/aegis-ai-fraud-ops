"""Base settings schema with common GCP and environment parameters."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class AegisBaseSettings(BaseSettings):
    """Core settings shared across Aegis microservices."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    gcp_project: str = "aegis-fraud-ops-2026"
    aegis_env: str = "local"
    aegis_adapter_mode: str = "mock"  # mock | gcp
    aegis_log_level: str = "INFO"
    gemini_api_key: str | None = None
    google_maps_api_key: str | None = None

    @property
    def clean_gemini_api_key(self) -> str | None:
        """Return clean Gemini API key free of whitespace or encoded artifacts."""
        key = self.gemini_api_key
        if not key:
            return None
        val = key.strip()
        parts = val.split()
        if len(parts) > 1 and all(p.isdigit() for p in parts):
            return "".join(chr(int(p)) for p in parts)
        return val

    @property
    def is_mock_mode(self) -> bool:
        """Return True if running offline with mock adapters."""
        return self.aegis_adapter_mode.lower() == "mock"
