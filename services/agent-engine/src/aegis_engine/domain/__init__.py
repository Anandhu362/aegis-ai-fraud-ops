"""Domain package exporting pure math, geolocation, scoring, and policy logic."""

from aegis_engine.domain.geo import (
    compute_haversine_distance,
    compute_travel_speed,
    evaluate_travel,
)
from aegis_engine.domain.policy import (
    decide_action,
    is_early_containment_candidate,
    map_score_to_risk_level,
)
from aegis_engine.domain.reports import (
    BehavioralReport,
    OrchestratorAssessment,
    ThreatReport,
)
from aegis_engine.domain.scoring import (
    apply_hard_rules,
    apply_llm_adjustment,
    calculate_full_score_breakdown,
    compute_base_score,
    evaluate_signals,
)
from aegis_engine.domain.velocity import (
    compute_monetary_anomaly,
    compute_velocity_stats,
    is_in_structuring_band,
)

__all__ = [
    "BehavioralReport",
    "OrchestratorAssessment",
    "ThreatReport",
    "apply_hard_rules",
    "apply_llm_adjustment",
    "calculate_full_score_breakdown",
    "compute_base_score",
    "compute_haversine_distance",
    "compute_monetary_anomaly",
    "compute_travel_speed",
    "compute_velocity_stats",
    "decide_action",
    "evaluate_signals",
    "evaluate_travel",
    "is_early_containment_candidate",
    "is_in_structuring_band",
    "map_score_to_risk_level",
]
