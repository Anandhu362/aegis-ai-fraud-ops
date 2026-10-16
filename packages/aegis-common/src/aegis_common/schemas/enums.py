"""Domain enumerations for Aegis AI Fraud Ops."""

from enum import StrEnum


class InvestigationStatus(StrEnum):
    """Lifecycle status of a fraud investigation."""

    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    ACTION_TAKEN = "ACTION_TAKEN"
    FAILED = "FAILED"


class RiskLevel(StrEnum):
    """Categorical risk assessment."""

    LOW = "LOW"
    ELEVATED = "ELEVATED"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Decision(StrEnum):
    """Final automated fraud policy decision."""

    ALLOW = "ALLOW"
    REVIEW = "REVIEW"
    CHALLENGE_3DS = "CHALLENGE_3DS"
    CARD_SUSPENDED = "CARD_SUSPENDED"
    BLOCK_TX = "BLOCK_TX"
    LOCK_ACCOUNT = "LOCK_ACCOUNT"
    DECLINE_LOCKED = "DECLINE_LOCKED"


class Typology(StrEnum):
    """Identified fraud typology or pattern."""

    NONE = "NONE"
    ACCOUNT_TAKEOVER = "ACCOUNT_TAKEOVER"
    STRUCTURING = "STRUCTURING"
    CREDENTIAL_STUFFING = "CREDENTIAL_STUFFING"
    CARD_TESTING = "CARD_TESTING"
    MERCHANT_DEVIATION = "MERCHANT_DEVIATION"
    OTHER = "OTHER"


class AgentName(StrEnum):
    """Names of the multi-agent ensemble participants."""

    INTAKE = "Intake Gate"
    ENRICHMENT = "Enrichment Agent"
    TRIAGE = "Triage Gate"
    ORCHESTRATOR = "Orchestrator"
    BEHAVIORAL = "Behavioral Analyst"
    THREAT_INTEL = "Threat Intel"
    POLICY = "Policy Engine"
    ACTUATOR = "Actuator"
    DEEP_REVIEW = "Deep Review"


class TelemetryAction(StrEnum):
    """Action category emitted during investigation pipeline."""

    THOUGHT = "THOUGHT"
    TOOL_CALL = "TOOL_CALL"
    TOOL_RESULT = "TOOL_RESULT"
    FINDING = "FINDING"
    VERDICT = "VERDICT"
    ACTION = "ACTION"
    ERROR = "ERROR"


class Channel(StrEnum):
    """Payment transaction channel."""

    CARD_PRESENT = "CARD_PRESENT"
    ECOMMERCE = "ECOMMERCE"
    TRANSFER = "TRANSFER"
    ATM = "ATM"


class MerchantCategory(StrEnum):
    """Standardized merchant category classification."""

    COFFEE_SHOP = "coffee_shop"
    GROCERY = "grocery"
    RESTAURANT = "restaurant"
    FUEL = "fuel"
    RETAIL = "retail"
    ELECTRONICS = "electronics"
    TRAVEL = "travel"
    UTILITIES = "utilities"
    PHARMACY = "pharmacy"
    ENTERTAINMENT = "entertainment"
    # High-risk categories
    CRYPTOCURRENCY_BROKERAGE = "cryptocurrency_brokerage"
    GAMBLING = "gambling"
    MONEY_TRANSFER = "money_transfer"
    GIFT_CARDS = "gift_cards"
    WIRE_TRANSFER = "wire_transfer"


HIGH_RISK_MERCHANT_CATEGORIES: frozenset[MerchantCategory] = frozenset(
    {
        MerchantCategory.CRYPTOCURRENCY_BROKERAGE,
        MerchantCategory.GAMBLING,
        MerchantCategory.MONEY_TRANSFER,
        MerchantCategory.GIFT_CARDS,
        MerchantCategory.WIRE_TRANSFER,
    }
)


class DispatchChannel(StrEnum):
    """Channel for automated external security alerts."""

    WHATSAPP_REST = "WHATSAPP_REST"
    SMS = "SMS"
    EMAIL = "EMAIL"
    PUSH = "PUSH"
    LOG_ONLY = "LOG_ONLY"
