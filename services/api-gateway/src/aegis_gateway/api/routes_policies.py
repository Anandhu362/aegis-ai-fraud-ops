"""Policy guardrails and deterministic rule configuration endpoint."""

# ruff: noqa: E501, RUF001

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/v1/policies", tags=["policies"])


class RuleDefinition(BaseModel):
    rule_id: str
    name: str
    description: str
    risk_floor: int
    typology: str


class PolicyGuardrails(BaseModel):
    policy_version: str
    hard_floors: list[RuleDefinition]
    containment_rule: dict[str, object]
    risk_bands: dict[str, str]
    action_matrix: list[dict[str, str]]
    rate_limits: dict[str, object]


@router.get(
    "",
    response_model=PolicyGuardrails,
    summary="Get active deterministic risk policies and hard guardrails",
)
async def get_active_policies() -> PolicyGuardrails:
    """Retrieve active deterministic banking fraud rules, hard floors, and containment guardrails."""
    return PolicyGuardrails(
        policy_version="v1.1",
        hard_floors=[
            RuleDefinition(
                rule_id="H1",
                name="Tor Exit Node + Impossible Travel",
                description="Anonymous exit node combined with travel velocity exceeding 800 km/h.",
                risk_floor=90,
                typology="ACCOUNT_TAKEOVER",
            ),
            RuleDefinition(
                rule_id="H2",
                name="Structuring Velocity Burst",
                description="Near-threshold payments ($9,000–$9,999) or rapid velocity burst in 60s.",
                risk_floor=85,
                typology="SMURFING_STRUCTURING",
            ),
            RuleDefinition(
                rule_id="H3",
                name="High-Risk Category Deviation",
                description="Novel high-risk merchant (crypto/gambling) deviating from 90-day baseline.",
                risk_floor=80,
                typology="HIGH_RISK_MERCHANT",
            ),
        ],
        containment_rule={
            "description": "Autonomous customer account freeze is permitted ONLY if Threat Score >= 85 and 2+ distinct vectors match.",
            "min_score": 85,
            "min_vectors": 2,
            "required_actions": ["account_locked", "tx_blocked", "alert_dispatched"],
        },
        risk_bands={
            "LOW": "0 – 29 (Frictionless Fast-Path approval, < 700ms)",
            "ELEVATED": "30 – 69 (Step-up authentication / 3DS Challenge or Analyst Review)",
            "HIGH": "70 – 84 (Inline transaction block, audit telemetry dispatched)",
            "CRITICAL": "85 – 100 (Autonomous account freeze & emergency customer alert)",
        },
        action_matrix=[
            {"decision": "ALLOW", "trigger": "Score < 30", "friction": "Zero Customer Friction"},
            {"decision": "CHALLENGE_3DS", "trigger": "Score 30-69 or Novel Device", "friction": "One-Time Passcode"},
            {"decision": "BLOCK_TX", "trigger": "Score >= 70 or Velocity Burst", "friction": "Transaction Declined"},
            {"decision": "LOCK_ACCOUNT", "trigger": "Score >= 85 and 2+ Vectors", "friction": "Account Frozen"},
        ],
        rate_limits={
            "global_ingestion_limit_rpm": 60,
            "ai_evaluation_cap_rpm": 15,
            "degraded_mode_fallback": "Pure Deterministic Policy Engine",
            "idempotency_window_seconds": 60,
        },
    )
