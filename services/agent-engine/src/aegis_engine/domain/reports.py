"""Pydantic schemas for structured specialist and orchestrator agent outputs."""

from aegis_common.schemas.enums import Typology
from pydantic import BaseModel, ConfigDict, Field


class BehavioralReport(BaseModel):
    """Structured report produced by the Behavioral Analyst agent."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    monetary_risk_level: str = Field(description="LOW | ELEVATED | HIGH")
    is_structuring_suspected: bool = Field(description="True if smurfing pattern detected")
    behavioral_anomaly_score: int = Field(ge=0, le=100, description="Specialist score 0-100")
    findings: list[str] = Field(default_factory=list, description="List of qualitative findings")
    cited_features: list[str] = Field(
        default_factory=list,
        description="Features cited as evidence (e.g. monetary.z_score)",
    )


class ThreatReport(BaseModel):
    """Structured report produced by the Threat Intelligence agent."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    network_risk_level: str = Field(description="LOW | ELEVATED | HIGH | CRITICAL")
    is_tor: bool = Field(description="Tor exit node confirmed")
    is_vpn: bool = Field(description="Commercial VPN detected")
    is_impossible_travel: bool = Field(description="Physical travel impossible")
    threat_intel_score: int = Field(ge=0, le=100, description="Specialist score 0-100")
    findings: list[str] = Field(default_factory=list, description="List of qualitative findings")
    cited_features: list[str] = Field(
        default_factory=list,
        description="Features cited as evidence (e.g. travel.speed_kmh)",
    )


class OrchestratorAssessment(BaseModel):
    """Synthesis assessment produced by the Orchestrator agent."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    typology: Typology = Field(default=Typology.NONE, description="Classified fraud pattern")
    rationale: str = Field(description="Concise evidence-backed synthesis summary")
    score_adjustment: int = Field(
        default=0,
        ge=-10,
        le=10,
        description="Bounded score adjustment [-10, +10]",
    )
    cited_evidence: list[str] = Field(
        default_factory=list,
        description="Consolidated list of confirmed evidence pointers",
    )
