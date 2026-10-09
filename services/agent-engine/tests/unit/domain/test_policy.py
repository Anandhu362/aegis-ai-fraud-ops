"""Unit tests for decision policy and risk band thresholds."""

from aegis_common.schemas.enums import Decision, RiskLevel
from aegis_common.schemas.features import FeatureVector, IpReputation, TravelCheck
from aegis_engine.domain.policy import (
    decide_action,
    is_early_containment_candidate,
    map_score_to_risk_level,
)


def test_map_score_to_risk_level_boundaries() -> None:
    """Verify exact boundary conditions between risk bands."""
    assert map_score_to_risk_level(0) == RiskLevel.LOW
    assert map_score_to_risk_level(30) == RiskLevel.LOW
    assert map_score_to_risk_level(31) == RiskLevel.ELEVATED
    assert map_score_to_risk_level(70) == RiskLevel.ELEVATED
    assert map_score_to_risk_level(71) == RiskLevel.HIGH
    assert map_score_to_risk_level(85) == RiskLevel.HIGH
    assert map_score_to_risk_level(86) == RiskLevel.CRITICAL
    assert map_score_to_risk_level(100) == RiskLevel.CRITICAL


def test_decide_action_low_risk() -> None:
    """Low risk must result in ALLOW without actuation."""
    decision, should_actuate, action = decide_action(RiskLevel.LOW)
    assert decision == Decision.ALLOW
    assert should_actuate is False
    assert action.account_locked is False


def test_decide_action_elevated_risk() -> None:
    """Elevated risk must result in REVIEW without immediate actuation."""
    decision, should_actuate, action = decide_action(RiskLevel.ELEVATED)
    assert decision == Decision.REVIEW
    assert should_actuate is False
    assert action.account_locked is False


def test_decide_action_high_risk() -> None:
    """High risk must block transaction and alert customer."""
    decision, should_actuate, action = decide_action(RiskLevel.HIGH)
    assert decision == Decision.BLOCK_TX
    assert should_actuate is True
    assert action.tx_blocked is True
    assert action.alert_dispatched is True
    assert action.account_locked is False


def test_decide_action_critical_lockout() -> None:
    """Critical risk must command account lockout, tx blocking, and alert dispatch."""
    decision, should_actuate, action = decide_action(
        RiskLevel.CRITICAL,
        is_early_containment=True,
    )
    assert decision == Decision.LOCK_ACCOUNT
    assert should_actuate is True
    assert action.account_locked is True
    assert action.tx_blocked is True
    assert action.alert_dispatched is True
    assert action.dispatch_channel == "WHATSAPP_REST"
    assert action.early_containment is True


def test_decide_action_already_locked_account() -> None:
    """An already locked account must short-circuit to DECLINE_LOCKED."""
    decision, should_actuate, action = decide_action(
        RiskLevel.LOW,
        is_account_locked=True,
    )
    assert decision == Decision.DECLINE_LOCKED
    assert should_actuate is False
    assert action.account_locked is True


def test_early_containment_candidate_detection() -> None:
    """Tor exit node combined with impossible travel must trigger early containment."""
    features_tor_travel = FeatureVector(
        ip=IpReputation(is_tor=True),
        travel=TravelCheck(impossible=True, speed_kmh=12000.0),
    )
    assert is_early_containment_candidate(features_tor_travel) is True

    features_tor_only = FeatureVector(
        ip=IpReputation(is_tor=True),
        travel=TravelCheck(impossible=False, speed_kmh=45.0),
    )
    assert is_early_containment_candidate(features_tor_only) is False
