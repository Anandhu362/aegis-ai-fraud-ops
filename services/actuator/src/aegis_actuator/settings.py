"""Settings for actuator service."""

from aegis_common.settings_base import AegisBaseSettings


class ActuatorSettings(AegisBaseSettings):
    """Configuration for actuator service."""

    aegis_notifier: str = "log"  # log | whatsapp
    aegis_port: int = 8070
