"""EnrichmentAgent: Parallel deterministic tool execution and early containment."""

import asyncio
import time
from collections.abc import AsyncGenerator

from aegis_common.schemas.enums import HIGH_RISK_MERCHANT_CATEGORIES, TelemetryAction
from aegis_common.schemas.features import (
    CategoryCheck,
    DeviceCheck,
    FeatureVector,
    GeoCheck,
)
from aegis_common.schemas.transaction import Transaction
from aegis_common.schemas.verdict import ScoreBreakdown
from google.adk.agents import BaseAgent, InvocationContext
from google.adk.events import Event, EventActions

from aegis_engine.application.telemetry import TelemetryEmitter
from aegis_engine.domain.scoring import apply_hard_rules, compute_base_score
from aegis_engine.domain.velocity import compute_monetary_anomaly
from aegis_engine.ports.actuator import ActuatorPort
from aegis_engine.ports.ip_intel import IpIntelPort
from aegis_engine.ports.profile_store import ProfileStore
from aegis_engine.tools.baseline import get_user_baseline
from aegis_engine.tools.device import check_device
from aegis_engine.tools.ip_reputation import lookup_ip_reputation
from aegis_engine.tools.travel import verify_velocity_travel
from aegis_engine.tools.velocity import get_velocity_window


class EnrichmentAgent(BaseAgent):
    """Deterministic enrichment agent executing parallel tool lookups and early containment."""

    def __init__(
        self,
        name: str = "enrichment",
        profile_store: ProfileStore | None = None,
        ip_intel: IpIntelPort | None = None,
        actuator: ActuatorPort | None = None,
    ) -> None:
        super().__init__(name=name)
        self._profile_store = profile_store
        self._ip_intel = ip_intel
        self._actuator = actuator

    async def _run_async_impl(  # noqa: PLR0915
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        """Query tools concurrently, assemble FeatureVector, and handle early containment.

        Args:
            ctx: ADK InvocationContext containing session state.

        Yields:
            Event with state_delta containing enriched features and score breakdown.
        """
        start_time = time.perf_counter()
        tx: Transaction = ctx.session.state["tx"]
        profile_store = self._profile_store or ctx.session.state.get("profile_store")
        ip_intel = self._ip_intel or ctx.session.state.get("ip_intel")
        actuator = self._actuator or ctx.session.state.get("actuator")
        emitter: TelemetryEmitter | None = ctx.session.state.get("emitter")

        if not profile_store:
            raise RuntimeError("EnrichmentAgent: Missing ProfileStore dependency")
        if not ip_intel:
            raise RuntimeError("EnrichmentAgent: Missing IpIntelPort dependency")

        # 1. Execute all 5 deterministic tool queries concurrently via asyncio.gather
        baseline_task = get_user_baseline(tx.user_id, profile_store)
        velocity_task = get_velocity_window(
            user_id=tx.user_id,
            current_amount=float(tx.amount),
            current_ts=tx.timestamp,
            profile_store=profile_store,
        )
        ip_task = lookup_ip_reputation(str(tx.ip_address) if tx.ip_address else None, ip_intel)
        lat = tx.location.latitude if tx.location else 0.0
        lon = tx.location.longitude if tx.location else 0.0
        travel_task = verify_velocity_travel(
            user_id=tx.user_id,
            current_lat=lat,
            current_lon=lon,
            current_ts=tx.timestamp,
            current_channel=tx.channel,
            profile_store=profile_store,
        )
        device_task = check_device(tx.user_id, tx.device_id, profile_store)

        (
            baseline,
            velocity,
            ip,
            travel,
            device_check,
        ) = await asyncio.gather(
            baseline_task,
            velocity_task,
            ip_task,
            travel_task,
            device_task,
        )

        # Record incoming transaction into rolling profile window
        if profile_store:
            loc_dict = None
            if tx.location:
                loc_dict = {
                    "lat": tx.location.latitude,
                    "lon": tx.location.longitude,
                    "city": tx.location.city or "",
                    "country": tx.location.country or "US",
                    "channel": tx.channel,
                }
            await profile_store.record_transaction(
                user_id=tx.user_id,
                amount=float(tx.amount),
                timestamp=tx.timestamp,
                location=loc_dict,
                device_id=tx.device_id,
            )

        # 2. Compute monetary and category anomaly metrics
        monetary = compute_monetary_anomaly(float(tx.amount), baseline)

        is_novel = tx.merchant_category.value not in baseline.known_categories
        is_high_risk = tx.merchant_category in HIGH_RISK_MERCHANT_CATEGORIES
        category = CategoryCheck(is_novel=is_novel, is_high_risk=is_high_risk)

        # 3. Geo mismatch check
        tx_country = tx.location.country.upper() if (tx.location and tx.location.country) else None
        ip_country = ip.country.upper() if ip.country else None
        country_mismatch = bool(
            tx_country and ip_country and tx_country != ip_country and not ip.unknown
        )
        geo = GeoCheck(country_mismatch=country_mismatch)

        # 4. Construct Composite FeatureVector
        features = FeatureVector(
            baseline=baseline,
            monetary=monetary,
            category=category,
            velocity=velocity,
            ip=ip,
            travel=travel,
            device=DeviceCheck(is_new=device_check.is_new),
            geo=geo,
        )

        # 5. Deterministic Scoring & Hard-Rule Evaluation
        base_score, signals = compute_base_score(features, tx.merchant_category)
        score_after_floors, highest_floor, triggered_rules = apply_hard_rules(base_score, features)

        score_breakdown = ScoreBreakdown(
            base=base_score,
            floor=highest_floor,
            llm_adjustment=0,
            signals=signals,
            rules=triggered_rules,
        )

        latency_ms = int((time.perf_counter() - start_time) * 1000)

        # 6. Stream telemetry milestones
        if emitter:
            avg_s = f"${baseline.avg_amount:.2f}"
            std_s = f"${baseline.std_amount:.2f}"
            await emitter.emit(
                agent="Enrichment",
                action=TelemetryAction.TOOL_RESULT,
                message=(
                    f"Baseline fetched: avg {avg_s}, std dev {std_s}. "
                    f"Z-score = {monetary.z_score:+.2f}, Structuring = {velocity.structuring_hit}."
                ),
                severity="WARN" if monetary.is_anomalous or velocity.structuring_hit else "INFO",
                data={"z_score": monetary.z_score, "structuring_hit": velocity.structuring_hit},
                latency_ms=latency_ms // 2,
            )

            prev_c = travel.prev_city or "None"
            await emitter.emit(
                agent="Enrichment",
                action=TelemetryAction.TOOL_RESULT,
                message=(
                    f"Threat signals: Tor={ip.is_tor}, Speed={travel.speed_kmh:.0f} km/h "
                    f"({prev_c} -> {travel.distance_km:.0f} km in {travel.elapsed_min:.1f}m). "
                    f"New device={device_check.is_new}."
                ),
                severity="CRITICAL" if travel.impossible or ip.is_tor else "INFO",
                data={
                    "is_tor": ip.is_tor,
                    "speed_kmh": travel.speed_kmh,
                    "impossible": travel.impossible,
                    "is_new_device": device_check.is_new,
                },
                latency_ms=latency_ms // 2,
            )

        # 7. Early Containment: If H1 triggered, initiate immediate account lockout
        early_contained = False
        if "H1" in triggered_rules and actuator:
            early_contained = True
            lock_reason = (
                f"Aegis Early Containment: H1 Tor Exit + Impossible Travel "
                f"({travel.speed_kmh:.0f} km/h)"
            )
            await actuator.execute_account_lockout(
                user_id=tx.user_id,
                reason=lock_reason,
                case_id=tx.tx_id,
            )
            if emitter:
                await emitter.emit(
                    agent="Policy Engine",
                    action=TelemetryAction.ACTION,
                    message=f"Hard rule H1 fired (Tor + {travel.speed_kmh:.0f} km/h). "
                    f"Early account lockout initiated immediately.",
                    severity="CRITICAL",
                    data={"rule": "H1", "early_containment": True},
                )

        yield Event(
            author=self.name,
            actions=EventActions(
                state_delta={
                    "features": features,
                    "base_score": score_after_floors,
                    "score_breakdown": score_breakdown,
                    "base_after_rules": score_after_floors,
                    "triggered_rules": triggered_rules,
                    "early_contained": early_contained,
                    "enrichment_latency_ms": latency_ms,
                }
            ),
        )
