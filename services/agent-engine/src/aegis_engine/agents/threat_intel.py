"""ThreatIntelAgent: Specialist evaluating network reputation, impossible travel, and devices."""

import os
import time
from collections.abc import AsyncGenerator

from aegis_common.logging import get_logger
from aegis_common.schemas.enums import TelemetryAction
from aegis_common.schemas.features import FeatureVector
from google import genai
from google.adk.agents import BaseAgent, InvocationContext
from google.adk.events import Event, EventActions
from google.genai import types

from aegis_engine.application.telemetry import TelemetryEmitter
from aegis_engine.domain.reports import ThreatReport
from aegis_engine.settings import EngineSettings

logger = get_logger("aegis.agent.threat_intel")

HIGH_SPEED_KMH_THRESHOLD: float = 800.0
ELEVATED_SPEED_KMH_THRESHOLD: float = 500.0
ELEVATED_ABUSE_SCORE_THRESHOLD: int = 50


def _evaluate_travel_signals(
    features: FeatureVector,
) -> tuple[bool, list[str], list[str], int]:
    is_travel = features.travel.impossible or features.travel.speed_kmh > HIGH_SPEED_KMH_THRESHOLD
    findings: list[str] = []
    cited: list[str] = []
    pts = 0
    if is_travel:
        sp = features.travel.speed_kmh
        dist = features.travel.distance_km
        el = features.travel.elapsed_min
        findings.append(
            f"Physically impossible travel velocity: {sp:.0f} km/h "
            f"across {dist:.0f} km in {el:.1f} minutes"
        )
        cited.append("travel.speed_kmh")
        pts += 40
    elif features.travel.speed_kmh > ELEVATED_SPEED_KMH_THRESHOLD:
        findings.append(f"High travel speed: {features.travel.speed_kmh:.0f} km/h")
        cited.append("travel.speed_kmh")
        pts += 15
    return is_travel, findings, cited, pts


def create_deterministic_threat_report(features: FeatureVector) -> ThreatReport:
    """Produce a deterministic ThreatReport from precomputed features."""
    is_tor = features.ip.is_tor
    is_vpn = features.ip.is_vpn
    is_new_device = features.device.is_new
    abuse = features.ip.abuse_score

    findings: list[str] = []
    cited: list[str] = []

    if is_tor:
        findings.append("Confirmed connection originating from known Tor exit node")
        cited.append("ip.is_tor")
        net_risk = "CRITICAL"
    elif is_vpn:
        findings.append("Commercial VPN or proxy network detected")
        cited.append("ip.is_vpn")
        net_risk = "MEDIUM"
    elif abuse >= ELEVATED_ABUSE_SCORE_THRESHOLD:
        findings.append(f"Elevated IP abuse reputation score: {abuse}/100")
        cited.append("ip.abuse_score")
        net_risk = "HIGH"
    else:
        net_risk = "LOW"

    is_travel, travel_findings, travel_cited, travel_pts = _evaluate_travel_signals(features)
    findings.extend(travel_findings)
    cited.extend(travel_cited)

    if is_new_device:
        findings.append("New unrecognized device hardware fingerprint")
        cited.append("device.is_new")

    if features.geo.country_mismatch:
        findings.append("Transaction origin country does not match IP registration country")
        cited.append("geo.country_mismatch")

    points = travel_pts
    if is_tor:
        points += 35
    elif is_vpn:
        points += 15

    if is_new_device:
        points += 15
    if features.geo.country_mismatch:
        points += 10

    score = min(100, points)

    return ThreatReport(
        network_risk_level=net_risk,
        is_tor=is_tor,
        is_vpn=is_vpn,
        is_impossible_travel=is_travel,
        threat_intel_score=score,
        findings=findings,
        cited_features=cited,
    )


class ThreatIntelAgent(BaseAgent):
    """Threat intelligence agent that classifies network, travel, and device vectors."""

    def __init__(self, name: str = "threat_intel", settings: EngineSettings | None = None) -> None:
        super().__init__(name=name)
        self._settings = settings or EngineSettings()

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        """Generate structured ThreatReport using Gemini or deterministic fallback."""
        start_time = time.perf_counter()
        triage = ctx.session.state.get("triage", "INVESTIGATE")
        features: FeatureVector = ctx.session.state.get("features", FeatureVector())
        emitter: TelemetryEmitter | None = ctx.session.state.get("emitter")

        # Fast-Path: If clean, skip inference and return baseline clean threat report
        if triage == "FAST_ALLOW":
            clean_report = ThreatReport(
                network_risk_level="LOW",
                is_tor=False,
                is_vpn=False,
                is_impossible_travel=False,
                threat_intel_score=0,
                findings=[
                    "Clean IP network. Known registered device. Feasible geographic location."
                ],
                cited_features=[],
            )
            yield Event(
                author=self.name,
                actions=EventActions(state_delta={"threat_report": clean_report}),
            )
            return

        report: ThreatReport | None = None

        # Live Gemini LLM execution if configured and not in offline mock mode
        api_key = (
            self._settings.clean_gemini_api_key or os.environ.get("GEMINI_API_KEY", "").strip()
        )
        if api_key and "\n" in api_key:
            parts = api_key.split()
            if len(parts) > 1 and all(p.isdigit() for p in parts):
                api_key = "".join(chr(int(p)) for p in parts)
        if not self._settings.is_mock_mode and api_key:
            try:
                client = genai.Client(api_key=api_key)
                prompt = (
                    "You are the Aegis Threat Intelligence AI.\n"
                    "Analyze the following network, travel, and device features:\n"
                    "<features>\n"
                    f"Is Tor: {features.ip.is_tor}\n"
                    f"Is VPN: {features.ip.is_vpn}\n"
                    f"Abuse Score: {features.ip.abuse_score}\n"
                    f"Travel Speed km/h: {features.travel.speed_kmh}\n"
                    f"Travel Distance km: {features.travel.distance_km}\n"
                    f"Travel Elapsed min: {features.travel.elapsed_min}\n"
                    f"Travel Impossible: {features.travel.impossible}\n"
                    f"New Device: {features.device.is_new}\n"
                    f"Country Mismatch: {features.geo.country_mismatch}\n"
                    "</features>\n"
                    "Return strictly JSON with keys:\n"
                    "- network_risk_level ('LOW' | 'ELEVATED' | 'HIGH')\n"
                    "- is_tor (boolean)\n"
                    "- is_vpn (boolean)\n"
                    "- is_impossible_travel (boolean)\n"
                    "- threat_intel_score (integer 0-100)\n"
                    "- findings (list of strings)\n"
                    "- cited_features (list of strings)"
                )

                config = types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.0,
                )

                logger.info(
                    "Invoking Gemini Threat Intel Specialist",
                    model=self._settings.aegis_model_specialist,
                )
                resp = client.models.generate_content(
                    model=self._settings.aegis_model_specialist,
                    contents=prompt,
                    config=config,
                )
                if resp.text:
                    report = ThreatReport.model_validate_json(resp.text)
                    logger.info(
                        "Gemini Threat Intel completed successfully",
                        score=report.threat_intel_score,
                    )
            except Exception as exc:
                logger.warn("Gemini Threat Intel failed, using fallback", error=str(exc))
                report = None

        # Deterministic fallback if mock mode or LLM failed
        if report is None:
            report = create_deterministic_threat_report(features)

        latency_ms = int((time.perf_counter() - start_time) * 1000)

        if emitter:
            findings_summary = (
                "; ".join(report.findings[:2]) if report.findings else "Clean network"
            )
            msg = (
                f"Threat Level: {report.network_risk_level} "
                f"(Score {report.threat_intel_score}/100). "
                f"Tor={report.is_tor}, Impossible Travel={report.is_impossible_travel}. "
                f"{findings_summary}"
            )
            await emitter.emit(
                agent="Threat Intel",
                action=TelemetryAction.FINDING,
                message=msg,
                severity="CRITICAL" if report.is_tor or report.is_impossible_travel else "INFO",
                data={
                    "score": report.threat_intel_score,
                    "network_risk": report.network_risk_level,
                    "is_tor": report.is_tor,
                    "impossible_travel": report.is_impossible_travel,
                    "findings": report.findings,
                    "cited_features": report.cited_features,
                },
                latency_ms=latency_ms,
            )

        yield Event(
            author=self.name,
            actions=EventActions(state_delta={"threat_report": report}),
        )
