"""Deterministic decision policy mapping threat scores to actions and containment."""

from aegis_common.schemas.enums import Decision, RiskLevel
from aegis_common.schemas.features import FeatureVector
from aegis_common.schemas.verdict import ActuatorAction

BAND_LOW_MAX: int = 30
BAND_ELEVATED_MAX: int = 70
BAND_HIGH_MAX: int = 85


def map_score_to_risk_level(threat_score: int) -> RiskLevel:
    """Map composite threat score [0, 100] to categorical RiskLevel.

    Args:
        threat_score: 0-100 composite threat score.

    Returns:
        RiskLevel (LOW, ELEVATED, HIGH, or CRITICAL).
    """
    if threat_score <= BAND_LOW_MAX:
        return RiskLevel.LOW
    if threat_score <= BAND_ELEVATED_MAX:
        return RiskLevel.ELEVATED
    if threat_score <= BAND_HIGH_MAX:
        return RiskLevel.HIGH
    return RiskLevel.CRITICAL


def decide_action(
    risk_level: RiskLevel,
    is_account_locked: bool = False,
    is_early_containment: bool = False,
) -> tuple[Decision, bool, ActuatorAction]:
    """Determine the final automated policy decision and actuation directives.

    Args:
        risk_level: Categorical risk level.
        is_account_locked: True if account is already locked in core banking.
        is_early_containment: True if early containment triggered before verdict.

    Returns:
        Tuple of (Decision, should_actuate_flag, ActuatorAction).
    """
    # H3: Fast-path decline if account already locked
    if is_account_locked:
        return (
            Decision.DECLINE_LOCKED,
            False,
            ActuatorAction(
                account_locked=True,
                tx_blocked=True,
                alert_dispatched=False,
                dispatch_channel="LOG_ONLY",
            ),
        )

    match risk_level:
        case RiskLevel.LOW:
            return (
                Decision.ALLOW,
                False,
                ActuatorAction(
                    account_locked=False,
                    tx_blocked=False,
                    alert_dispatched=False,
                    dispatch_channel="LOG_ONLY",
                ),
            )

        case RiskLevel.ELEVATED:
            return (
                Decision.REVIEW,
                False,
                ActuatorAction(
                    account_locked=False,
                    tx_blocked=False,
                    alert_dispatched=False,
                    dispatch_channel="LOG_ONLY",
                ),
            )

        case RiskLevel.HIGH:
            return (
                Decision.BLOCK_TX,
                True,
                ActuatorAction(
                    account_locked=False,
                    tx_blocked=True,
                    alert_dispatched=True,
                    dispatch_channel="SMS",
                ),
            )

        case RiskLevel.CRITICAL:
            return (
                Decision.LOCK_ACCOUNT,
                True,
                ActuatorAction(
                    account_locked=True,
                    tx_blocked=True,
                    alert_dispatched=True,
                    dispatch_channel="WHATSAPP_REST",
                    early_containment=is_early_containment,
                ),
            )


EARLY_CONTAINMENT_SPEED_KMH: float = 800.0


def is_early_containment_candidate(features: FeatureVector) -> bool:
    """Return True if conditions warrant immediate account freeze during enrichment stage."""
    return features.ip.is_tor and (
        features.travel.impossible or features.travel.speed_kmh > EARLY_CONTAINMENT_SPEED_KMH
    )
