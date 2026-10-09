"""Unit tests for deterministic scoring, hard-rule floors, and bounded adjustments."""

from aegis_common.schemas.enums import MerchantCategory
from aegis_common.schemas.features import (
    CategoryCheck,
    DeviceCheck,
    FeatureVector,
    GeoCheck,
    IpReputation,
    MonetaryAnomaly,
    TravelCheck,
    UserBaseline,
    VelocityStats,
)
from aegis_engine.domain.scoring import (
    apply_hard_rules,
    apply_llm_adjustment,
    calculate_full_score_breakdown,
    compute_base_score,
    evaluate_signals,
)


def test_clean_coffee_zero_score() -> None:
    """A regular coffee transaction at a known merchant category must yield score 0."""
    features = FeatureVector(
        baseline=UserBaseline(known_categories=["coffee_shop"]),
        monetary=MonetaryAnomaly(z_score=0.2),
        category=CategoryCheck(is_novel=False, is_high_risk=False),
        velocity=VelocityStats(count_60s=1, count_15m=1),
        ip=IpReputation(is_tor=False, is_vpn=False),
        travel=TravelCheck(impossible=False, speed_kmh=15.0),
        device=DeviceCheck(is_new=False),
        geo=GeoCheck(country_mismatch=False),
    )

    score, breakdown = calculate_full_score_breakdown(
        features,
        MerchantCategory.COFFEE_SHOP,
        llm_adjustment=0,
    )

    assert score == 0
    assert breakdown.base == 0
    assert breakdown.floor == 0
    assert len(breakdown.rules) == 0


def test_individual_signals_coverage() -> None:
    """Ensure all individual signals S1-S10 trigger their respective weights."""
    # S1 tier 2: z=3.5 -> 20 pts
    features_z3 = FeatureVector(
        baseline=UserBaseline(known_categories=["retail"]),
        monetary=MonetaryAnomaly(z_score=3.5),
    )
    sig_z3 = evaluate_signals(features_z3, MerchantCategory.RETAIL)
    assert sig_z3.get("S1_monetary") == 20

    # S1 tier 3: z=2.5 -> 10 pts
    features_z2 = FeatureVector(
        baseline=UserBaseline(known_categories=["retail"]),
        monetary=MonetaryAnomaly(z_score=2.5),
    )
    sig_z2 = evaluate_signals(features_z2, MerchantCategory.RETAIL)
    assert sig_z2.get("S1_monetary") == 10

    # Signals S2 (novel), S3 (high risk), S5 (burst), S6 (VPN), S7 (abuse)
    # S8 (travel speed), S9 (geo mismatch), S10 (new device)
    features_full = FeatureVector(
        baseline=UserBaseline(known_categories=["grocery"]),
        monetary=MonetaryAnomaly(z_score=4.5),  # S1 -> 25
        category=CategoryCheck(is_novel=True, is_high_risk=True),
        velocity=VelocityStats(count_60s=6, in_structuring_band=True),  # S5 -> 15, S4 in band -> 10
        ip=IpReputation(is_tor=False, is_vpn=True, abuse_score=60),  # S6 -> 15, S7 -> 10
        travel=TravelCheck(speed_kmh=650.0, exempt=False),  # S8 -> 15
        device=DeviceCheck(is_new=True),  # S10 -> 10
        geo=GeoCheck(country_mismatch=True),  # S9 -> 8
    )

    signals = evaluate_signals(features_full, MerchantCategory.CRYPTOCURRENCY_BROKERAGE)
    assert signals["S1_monetary"] == 25
    assert signals["S2_novel_category"] == 8
    assert signals["S3_high_risk_category"] == 7
    assert signals["S4_structuring"] == 10
    assert signals["S5_velocity_burst"] == 15
    assert signals["S6_anon_network"] == 15
    assert signals["S7_ip_abuse"] == 10
    assert signals["S8_travel"] == 15
    assert signals["S9_geo_mismatch"] == 8
    assert signals["S10_new_device"] == 10


def test_hard_rule_h1_tor_impossible_travel() -> None:
    """Tor exit node + impossible travel must trigger H1 floor (>= 90)."""
    features = FeatureVector(
        ip=IpReputation(is_tor=True),
        travel=TravelCheck(impossible=True, speed_kmh=12000.0),
    )

    base, _signals = compute_base_score(features, MerchantCategory.RETAIL)
    score_after, floor, rules = apply_hard_rules(base, features)

    assert "H1" in rules
    assert floor == 90
    assert score_after >= 90


def test_hard_rule_h2_structuring() -> None:
    """Structuring hit must trigger H2 floor (>= 72)."""
    features = FeatureVector(
        velocity=VelocityStats(structuring_hit=True),
    )

    base, _ = compute_base_score(features, MerchantCategory.RETAIL)
    score_after, floor, rules = apply_hard_rules(base, features)

    assert "H2" in rules
    assert floor == 72
    assert score_after >= 72


def test_llm_adjustment_clamped_bounds() -> None:
    """LLM adjustments beyond [-10, +10] must be clamped strictly in Python."""
    final_high, adj_high = apply_llm_adjustment(50, 25, hard_floor=0)
    assert adj_high == 10
    assert final_high == 60

    final_low, adj_low = apply_llm_adjustment(50, -25, hard_floor=0)
    assert adj_low == -10
    assert final_low == 40


def test_llm_adjustment_cannot_violate_hard_floor() -> None:
    """An LLM adjustment can NEVER reduce the final score below a triggered hard floor."""
    final, adj = apply_llm_adjustment(90, -10, hard_floor=90)
    assert adj == -10
    assert final == 90
