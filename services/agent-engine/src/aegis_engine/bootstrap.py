"""Composition root for agent-engine service."""

from aegis_engine.adapters.gcp import FirestoreTelemetrySinkAdapter
from aegis_engine.adapters.mock import (
    InMemoryProfileStore,
    MockActuatorAdapter,
    MockTelemetrySinkAdapter,
    StaticIpIntelAdapter,
)
from aegis_engine.application.run_investigation import InvestigationService
from aegis_engine.ports.actuator import ActuatorPort
from aegis_engine.ports.ip_intel import IpIntelPort
from aegis_engine.ports.profile_store import ProfileStore
from aegis_engine.ports.telemetry_sink import TelemetrySinkPort
from aegis_engine.settings import EngineSettings


class EngineContainer:
    """Dependency container holding ports and services for agent-engine."""

    def __init__(
        self,
        service: InvestigationService,
        profile_store: ProfileStore,
        ip_intel: IpIntelPort,
        actuator: ActuatorPort,
        telemetry_sink: TelemetrySinkPort,
    ) -> None:
        self.service = service
        self.profile_store = profile_store
        self.ip_intel = ip_intel
        self.actuator = actuator
        self.telemetry_sink = telemetry_sink


def build_engine(settings: EngineSettings) -> EngineContainer:
    """Build the investigation engine container based on configured adapter mode.

    Args:
        settings: Active runtime engine settings.

    Returns:
        EngineContainer with wired ports and InvestigationService.
    """
    profile_store = InMemoryProfileStore()
    ip_intel = StaticIpIntelAdapter()
    actuator = MockActuatorAdapter()

    telemetry_sink: TelemetrySinkPort
    if settings.is_mock_mode:
        telemetry_sink = MockTelemetrySinkAdapter()
    else:
        try:
            telemetry_sink = FirestoreTelemetrySinkAdapter(
                project_id=settings.gcp_project,
                bq_dataset=settings.aegis_bq_dataset,
            )
        except Exception:
            telemetry_sink = MockTelemetrySinkAdapter()

    service = InvestigationService(
        profile_store=profile_store,
        ip_intel=ip_intel,
        actuator=actuator,
        telemetry_sink=telemetry_sink,
        settings=settings,
    )

    return EngineContainer(
        service=service,
        profile_store=profile_store,
        ip_intel=ip_intel,
        actuator=actuator,
        telemetry_sink=telemetry_sink,
    )
