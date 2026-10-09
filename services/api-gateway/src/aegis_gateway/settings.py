"""Configuration settings for api-gateway."""

from aegis_common.settings_base import AegisBaseSettings


class GatewaySettings(AegisBaseSettings):
    """Settings specific to api-gateway service."""

    aegis_analyze_mode: str = "sync"  # async | sync
    aegis_engine_url: str = "http://localhost:8090"
    aegis_actuator_url: str = "http://localhost:8070"
    aegis_rate_limit_rps: int = 20
    aegis_port: int = 8080
