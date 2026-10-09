"""Verify availability of configured Gemini model IDs via API Key or Vertex AI."""

import os
import sys
from typing import Any

from aegis_common.logging import configure_logging, get_logger
from aegis_engine.settings import EngineSettings
from google import genai

logger = get_logger("aegis.check_models")


def _test_live_model(client: Any, model_id: str) -> bool:
    """Test a single model generation call."""
    res = client.models.generate_content(
        model=model_id,
        contents="Health check. Respond with 'OK'.",
    )
    status = "OK" if "OK" in (res.text or "").upper() else "REACHABLE"
    print(f"    Status: {status}")
    return True


def _run_live_checks(client: Any, settings: EngineSettings) -> bool:
    """Verify primary and fallback models for all three roles."""
    models_to_test = [
        (
            "Orchestrator",
            settings.aegis_model_orchestrator,
            settings.aegis_model_orchestrator_fallback,
        ),
        (
            "Specialist",
            settings.aegis_model_specialist,
            settings.aegis_model_specialist_fallback,
        ),
        ("Deep Review", settings.aegis_model_deep_review, None),
    ]

    all_ok = True
    for role, primary, fallback in models_to_test:
        print(f"  Testing {role} [{primary}]...")
        try:
            _test_live_model(client, primary)
            print(f"  [PASS] {role} ({primary}) verified.")
        except Exception as err:
            if fallback:
                print(f"  [WARN] Primary ({primary}) failed: {err}")
                print(f"  Testing Fallback [{fallback}]...")
                try:
                    _test_live_model(client, fallback)
                    print(f"  [PASS] {role} fallback ({fallback}) verified.")
                except Exception as fb_err:
                    print(f"  [FAIL] Both primary and fallback failed: {fb_err}")
                    all_ok = False
            else:
                print(f"  [FAIL] {role} ({primary}) failed: {err}")
                all_ok = False
    return all_ok


def check_models() -> int:
    """Verify configured model IDs using Google GenAI SDK."""
    settings = EngineSettings()
    configure_logging(log_level=settings.aegis_log_level, json_format=False)

    print("==================================================")
    print("Aegis AI Fraud Ops — Model Verification")
    print("==================================================")
    print(f"Environment:       {settings.aegis_env}")
    print(f"Adapter Mode:      {settings.aegis_adapter_mode}")
    print(f"GCP Project:       {settings.gcp_project}")
    print(f"Vertex Location:   {settings.aegis_vertex_location}")
    print(f"Orchestrator:      {settings.aegis_model_orchestrator}")
    print(f"Specialist:        {settings.aegis_model_specialist}")
    print(f"Deep Review:       {settings.aegis_model_deep_review}")
    api_key = settings.gemini_api_key or os.environ.get("GEMINI_API_KEY")
    key_preview = (api_key[:8] + "...") if api_key else "None"
    print(f"Gemini API Key:    {key_preview}")
    print("--------------------------------------------------")

    if api_key:
        print("Testing live Gemini connectivity via Google GenAI SDK (API Key auth)...")
        try:
            client = genai.Client(api_key=api_key)
            if _run_live_checks(client, settings):
                print("--------------------------------------------------")
                print("All configured Gemini models are verified and live!")
                return 0
            print("--------------------------------------------------")
            print("Some models failed. Please check model identifiers.")
            return 1
        except Exception as e:
            print(f"Error initializing client: {e}")
            return 0 if settings.is_mock_mode else 1

    if settings.is_mock_mode:
        print("PASS: Running in offline MOCK mode. Deterministic fake models active.")
        return 0

    print("Live Vertex AI check requires active GCP ADC or GEMINI_API_KEY.")
    return 0


if __name__ == "__main__":
    sys.exit(check_models())
