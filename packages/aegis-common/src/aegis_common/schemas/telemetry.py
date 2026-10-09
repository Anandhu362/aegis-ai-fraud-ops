"""Telemetry event schema for real-time investigation streaming to Firestore."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from aegis_common.schemas.enums import TelemetryAction


class TelemetryEvent(BaseModel):
    """An ordered telemetry milestone emitted during agent pipeline execution."""

    model_config = ConfigDict(frozen=True)

    seq: int = Field(
        ge=0, description="Strict monotonically increasing sequence number (0, 1, 2...)"
    )
    agent: str = Field(description="Name of the agent emitting the event")
    action: TelemetryAction = Field(
        description="Type of event (THOUGHT, TOOL_CALL, TOOL_RESULT, etc.)"
    )
    severity: str = Field(default="INFO", description="INFO, WARN, or CRITICAL")
    message: str = Field(description="Human-readable terminal log line")
    data: dict[str, Any] = Field(
        default_factory=dict, description="Structured payload or tool arguments/result"
    )
    latency_ms: int = Field(default=0, description="Execution duration of this specific step in ms")
    timestamp: int = Field(description="Epoch timestamp in milliseconds")
