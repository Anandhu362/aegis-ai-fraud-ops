"""Configuration settings for agent-engine."""

from aegis_common.settings_base import AegisBaseSettings


class EngineSettings(AegisBaseSettings):
    """Settings specific to agent-engine ADK pipeline and models."""

    aegis_vertex_location: str = "global"
    aegis_model_orchestrator: str = "gemini-3-flash"
    aegis_model_orchestrator_fallback: str = "gemini-2.5-flash"
    aegis_model_specialist: str = "gemini-3-flash-lite"
    aegis_model_specialist_fallback: str = "gemini-2.5-flash-lite"
    aegis_model_deep_review: str = "gemini-3.1-pro"

    aegis_risk_policy_path: str = "config/risk_policy.yaml"
    aegis_timeout_pipeline_ms: int = 6000
    aegis_timeout_llm_ms: int = 1500
    aegis_actuator_url: str = "http://localhost:8070"
    aegis_port: int = 8090
