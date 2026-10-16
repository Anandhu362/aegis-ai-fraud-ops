"""BehavioralAnalystAgent: Specialist evaluating monetary deviations and structuring anomalies."""

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
from aegis_engine.domain.reports import BehavioralReport
from aegis_engine.settings import EngineSettings

logger = get_logger("aegis.agent.behavioral")

HIGH_Z_SCORE_THRESHOLD: float = 4.0
ELEVATED_Z_SCORE_THRESHOLD: float = 2.0
HIGH_P95_RATIO_THRESHOLD: float = 2.0
BURST_COUNT_60S_THRESHOLD: int = 5
WARN_ANOMALY_SCORE_THRESHOLD: int = 40


def create_deterministic_behavioral_report(features: FeatureVector) -> BehavioralReport:
    """Produce a deterministic BehavioralReport from precomputed features."""
    z = features.monetary.z_score
    r_p95 = features.monetary.ratio_to_p95
    structuring = features.velocity.structuring_hit
    burst = features.velocity.count_60s >= BURST_COUNT_60S_THRESHOLD
    novel_cat = features.category.is_novel

    findings: list[str] = []
    cited: list[str] = []

    if z >= HIGH_Z_SCORE_THRESHOLD:
        avg_amt = features.baseline.avg_amount
        findings.append(f"Extreme monetary deviation: Z-score is {z:+.2f} (>{avg_amt:.2f} avg)")
        cited.append("monetary.z_score")
        monetary_level = "HIGH"
    elif z >= ELEVATED_Z_SCORE_THRESHOLD:
        findings.append(f"Elevated monetary deviation: Z-score is {z:+.2f}")
        cited.append("monetary.z_score")
        monetary_level = "ELEVATED"
    else:
        monetary_level = "LOW"

    if r_p95 > HIGH_P95_RATIO_THRESHOLD:
        findings.append(f"Transaction is {r_p95:.1f}x the historical 95th percentile amount")
        cited.append("monetary.ratio_to_p95")

    if structuring:
        findings.append(
            "Structuring smurfing detected: Multiple near-threshold transactions "
            "within 15-minute window"
        )
        cited.append("velocity.structuring_hit")

    if burst:
        findings.append(
            f"High-frequency velocity burst: {features.velocity.count_60s} transactions in past 60s"
        )
        cited.append("velocity.count_60s")

    if novel_cat:
        findings.append("Novel merchant category never previously observed for this account")
        cited.append("category.is_novel")

    # Score synthesis 0-100
    points = 0
    if z >= HIGH_Z_SCORE_THRESHOLD:
        points += 35
    elif z >= ELEVATED_Z_SCORE_THRESHOLD:
        points += 15

    if structuring:
        points += 40
    elif features.velocity.in_structuring_band:
        points += 15

    if burst:
        points += 15
    if novel_cat:
        points += 10

    score = min(100, points)

    return BehavioralReport(
        monetary_risk_level=monetary_level,
        is_structuring_suspected=structuring,
        behavioral_anomaly_score=score,
        findings=findings,
        cited_features=cited,
    )


class BehavioralAnalystAgent(BaseAgent):
    """Behavioral analyst agent that interprets spending and velocity anomalies."""

    def __init__(
        self, name: str = "behavioral_analyst", settings: EngineSettings | None = None
    ) -> None:
        super().__init__(name=name)
        self._settings = settings or EngineSettings()

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        """Generate structured BehavioralReport using Gemini or deterministic fallback."""
        start_time = time.perf_counter()
        triage = ctx.session.state.get("triage", "INVESTIGATE")
        features: FeatureVector = ctx.session.state.get("features", FeatureVector())
        emitter: TelemetryEmitter | None = ctx.session.state.get("emitter")

        # Fast-Path: If clean, skip inference and return baseline clean report
        if triage == "FAST_ALLOW":
            clean_report = BehavioralReport(
                monetary_risk_level="LOW",
                is_structuring_suspected=False,
                behavioral_anomaly_score=0,
                findings=["Normal routine spending. No monetary or velocity anomaly detected."],
                cited_features=[],
            )
            yield Event(
                author=self.name,
                actions=EventActions(state_delta={"behavioral_report": clean_report}),
            )
            return

        report: BehavioralReport | None = None

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
                    "You are the Aegis Behavioral Analyst AI.\n"
                    "Analyze the following precomputed features:\n"
                    "<features>\n"
                    f"Monetary Z-score: {features.monetary.z_score}\n"
                    f"Ratio to P95: {features.monetary.ratio_to_p95}\n"
                    f"Category Novel: {features.category.is_novel}\n"
                    f"Category High Risk: {features.category.is_high_risk}\n"
                    f"Structuring Hit: {features.velocity.structuring_hit}\n"
                    f"Count 60s: {features.velocity.count_60s}\n"
                    "</features>\n"
                    "Return strictly JSON with keys:\n"
                    "- monetary_risk_level ('LOW' | 'ELEVATED' | 'HIGH')\n"
                    "- is_structuring_suspected (boolean)\n"
                    "- behavioral_anomaly_score (integer 0-100)\n"
                    "- findings (list of strings)\n"
                    "- cited_features (list of strings)"
                )

                config = types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.0,
                )

                logger.info(
                    "Invoking Gemini Behavioral Analyst Specialist",
                    model=self._settings.aegis_model_specialist,
                )
                resp = client.models.generate_content(
                    model=self._settings.aegis_model_specialist,
                    contents=prompt,
                    config=config,
                )
                if resp.text:
                    report = BehavioralReport.model_validate_json(resp.text)
                    logger.info(
                        "Gemini Behavioral Analyst completed successfully",
                        score=report.behavioral_anomaly_score,
                    )
            except Exception as exc:
                logger.warn("Gemini Behavioral Analyst failed, using fallback", error=str(exc))
                report = None

        # Deterministic fallback if mock mode or LLM failed
        if report is None:
            report = create_deterministic_behavioral_report(features)

        latency_ms = int((time.perf_counter() - start_time) * 1000)

        if emitter:
            findings_summary = (
                "; ".join(report.findings[:2]) if report.findings else "Normal behavior"
            )
            msg = (
                f"Monetary Risk: {report.monetary_risk_level} "
                f"(Score {report.behavioral_anomaly_score}/100). "
                f"Structuring={report.is_structuring_suspected}. "
                f"{findings_summary}"
            )
            await emitter.emit(
                agent="Behavioral Analyst",
                action=TelemetryAction.FINDING,
                message=msg,
                severity="WARN"
                if report.behavioral_anomaly_score >= WARN_ANOMALY_SCORE_THRESHOLD
                else "INFO",
                data={
                    "score": report.behavioral_anomaly_score,
                    "monetary_risk": report.monetary_risk_level,
                    "findings": report.findings,
                    "cited_features": report.cited_features,
                },
                latency_ms=latency_ms,
            )

        yield Event(
            author=self.name,
            actions=EventActions(state_delta={"behavioral_report": report}),
        )
