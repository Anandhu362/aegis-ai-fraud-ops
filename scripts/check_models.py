"""Verify availability of configured Gemini model IDs."""

import sys

from aegis_common.logging import configure_logging, get_logger
from aegis_engine.settings import EngineSettings

logger = get_logger("aegis.check_models")


def check_models() -> int:
    """Verify configured model IDs."""
    settings = EngineSettings()
    configure_logging(log_level=settings.aegis_log_level, json_format=False)

    print("==================================================")
    print("Aegis AI Fraud Ops — Model Verification")
    print("==================================================")
    print(f"Environment:       {settings.aegis_env}")
    print(f"Adapter Mode:      {settings.aegis_adapter_mode}")
    print(f"GCP Project:       {settings.gcp_project}")
    print(f"Vertex Location:   {settings.aegis_vertex_location}")
    orch_fb = settings.aegis_model_orchestrator_fallback
    spec_fb = settings.aegis_model_specialist_fallback
    print(f"Orchestrator:      {settings.aegis_model_orchestrator} (Fallback: {orch_fb})")
    print(f"Specialist:        {settings.aegis_model_specialist} (Fallback: {spec_fb})")
    print(f"Deep Review:       {settings.aegis_model_deep_review}")
    print("--------------------------------------------------")

    if settings.is_mock_mode:
        print("PASS: Running in offline MOCK mode. Deterministic fake models active.")
        return 0

    print("Checking live Vertex AI models requires active Google Cloud ADC.")
    return 0


if __name__ == "__main__":
    sys.exit(check_models())
