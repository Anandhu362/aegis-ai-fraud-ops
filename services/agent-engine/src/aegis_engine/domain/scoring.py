"""Deterministic risk scoring calculation, signal evaluation, and hard-rule floors."""

from aegis_common.schemas.enums import HIGH_RISK_MERCHANT_CATEGORIES, MerchantCategory
from aegis_common.schemas.features import FeatureVector
from aegis_common.schemas.verdict import ScoreBreakdown

MAX_SCORE: int = 100
MIN_SCORE: int = 0
MAX_ADJUSTMENT: int = 10
MIN_ADJUSTMENT: int = -10

FLOOR_H1_TOR_TRAVEL: int = 90
FLOOR_H2_STRUCTURING: int = 72

Z_TIER_1: float = 4.0
Z_TIER_2: float = 3.0
Z_TIER_3: float = 2.0
BURST_COUNT: int = 5
ABUSE_SCORE_THRESHOLD: int = 50
IMPOSSIBLE_SPEED_THRESHOLD: float = 800.0
ELEVATED_SPEED_THRESHOLD: float = 500.0


def evaluate_signals(
    features: FeatureVector,
    merchant_category: MerchantCategory,
) -> dict[str, int]:
    """Evaluate individual risk signals S1-S10 based on precomputed features.

    Args:
        features: Precomputed FeatureVector.
        merchant_category: Transaction merchant category.

    Returns:
        Mapping of signal identifiers to points awarded.
    """
    signals: dict[str, int] = {}

    # S1: Monetary anomaly
    z = features.monetary.z_score
    if z >= Z_TIER_1:
        signals["S1_monetary"] = 25
    elif z >= Z_TIER_2:
        signals["S1_monetary"] = 20
    elif z >= Z_TIER_3:
        signals["S1_monetary"] = 10

    # S2: Category novelty
    if merchant_category.value not in features.baseline.known_categories:
        signals["S2_novel_category"] = 8

    # S3: High-risk merchant category
    if merchant_category in HIGH_RISK_MERCHANT_CATEGORIES:
        signals["S3_high_risk_category"] = 7

    # S4: Structuring
    if features.velocity.structuring_hit:
        signals["S4_structuring"] = 35
    elif features.velocity.in_structuring_band:
        signals["S4_structuring"] = 10

    # S5: Velocity burst
    if features.velocity.count_60s >= BURST_COUNT:
        signals["S5_velocity_burst"] = 15

    # S6: Anonymized network (non-additive max)
    if features.ip.is_tor:
        signals["S6_anon_network"] = 30
    elif features.ip.is_vpn or features.ip.is_hosting:
        signals["S6_anon_network"] = 15

    # S7: IP abuse score
    if features.ip.abuse_score >= ABUSE_SCORE_THRESHOLD:
        signals["S7_ip_abuse"] = 10

    # S8: Impossible travel
    if features.travel.impossible or features.travel.speed_kmh > IMPOSSIBLE_SPEED_THRESHOLD:
        signals["S8_travel"] = 35
    elif features.travel.speed_kmh > ELEVATED_SPEED_THRESHOLD and not features.travel.exempt:
        signals["S8_travel"] = 15

    # S9: Country mismatch
    if features.geo.country_mismatch:
        signals["S9_geo_mismatch"] = 8

    # S10: Unrecognized device
    if features.device.is_new:
        signals["S10_new_device"] = 10

    return signals


def compute_base_score(
    features: FeatureVector,
    merchant_category: MerchantCategory,
) -> tuple[int, dict[str, int]]:
    """Compute the deterministic base score by summing all fired signal weights.

    Args:
        features: Precomputed FeatureVector.
        merchant_category: Transaction merchant category.

    Returns:
        Tuple of (base_score capped at 100, signals_dict).
    """
    signals = evaluate_signals(features, merchant_category)
    total_points = sum(signals.values())
    base_score = min(MAX_SCORE, total_points)
    return base_score, signals


def apply_hard_rules(
    base_score: int,
    features: FeatureVector,
) -> tuple[int, int, list[str]]:
    """Apply statutory and safety hard-rule risk floors over the base score.

    Args:
        base_score: Raw sum of signal points.
        features: Precomputed FeatureVector.

    Returns:
        Tuple of (score_after_floors, highest_floor, triggered_rule_ids).
    """
    rules: list[str] = []
    highest_floor = 0

    # H1: Tor exit AND impossible travel -> floor 90
    if features.ip.is_tor and (
        features.travel.impossible or features.travel.speed_kmh > IMPOSSIBLE_SPEED_THRESHOLD
    ):
        rules.append("H1")
        highest_floor = max(highest_floor, FLOOR_H1_TOR_TRAVEL)

    # H2: Structuring hit -> floor 72
    if features.velocity.structuring_hit:
        rules.append("H2")
        highest_floor = max(highest_floor, FLOOR_H2_STRUCTURING)

    score_after_floors = max(base_score, highest_floor)
    return score_after_floors, highest_floor, rules


def apply_llm_adjustment(
    score_after_rules: int,
    adjustment: int,
    hard_floor: int,
) -> tuple[int, int]:
    """Apply bounded orchestrator adjustment while strictly respecting hard floors.

    Args:
        score_after_rules: Score with hard-rule floors applied.
        adjustment: Suggested adjustment from Orchestrator agent.
        hard_floor: Highest active hard-rule floor.

    Returns:
        Tuple of (final_threat_score, bounded_adjustment_applied).
    """
    bounded_adj = max(MIN_ADJUSTMENT, min(MAX_ADJUSTMENT, adjustment))
    adjusted_score = score_after_rules + bounded_adj
    # Invariant: Score can NEVER drop below the hard-rule floor or range [0, 100]
    final_score = max(hard_floor, min(MAX_SCORE, max(MIN_SCORE, adjusted_score)))
    return final_score, bounded_adj


def calculate_full_score_breakdown(
    features: FeatureVector,
    merchant_category: MerchantCategory,
    llm_adjustment: int = 0,
) -> tuple[int, ScoreBreakdown]:
    """Execute complete deterministic scoring pipeline and produce audit breakdown.

    Args:
        features: Precomputed FeatureVector.
        merchant_category: Merchant category.
        llm_adjustment: Suggested adjustment from Orchestrator (default 0).

    Returns:
        Tuple of (final_score, ScoreBreakdown).
    """
    base_score, signals = compute_base_score(features, merchant_category)
    score_after_floors, highest_floor, rules = apply_hard_rules(base_score, features)
    final_score, bounded_adj = apply_llm_adjustment(
        score_after_floors,
        llm_adjustment,
        highest_floor,
    )

    breakdown = ScoreBreakdown(
        base=base_score,
        floor=highest_floor,
        llm_adjustment=bounded_adj,
        signals=signals,
        rules=rules,
    )
    return final_score, breakdown
