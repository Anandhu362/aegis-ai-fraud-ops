"""Aegis Agent Engine Application orchestration layer."""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from aegis_engine.application.run_investigation import InvestigationService
    from aegis_engine.application.telemetry import TelemetryEmitter


def __getattr__(name: str) -> Any:
    if name == "InvestigationService":
        from aegis_engine.application.run_investigation import InvestigationService  # noqa: PLC0415

        return InvestigationService
    if name == "TelemetryEmitter":
        from aegis_engine.application.telemetry import TelemetryEmitter  # noqa: PLC0415

        return TelemetryEmitter
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["InvestigationService", "TelemetryEmitter"]
