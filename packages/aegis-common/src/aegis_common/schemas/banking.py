"""Banking schemas for authentic enterprise customer and account data."""

from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from aegis_common.schemas.features import UserBaseline


class AccountType(StrEnum):
    """Deposit and credit account classifications."""

    CHECKING = "CHECKING"
    SAVINGS = "SAVINGS"
    CREDIT_LINE = "CREDIT_LINE"


class AccountStatus(StrEnum):
    """Core banking account operational lifecycle status."""

    ACTIVE = "ACTIVE"
    FROZEN = "FROZEN"
    LOCKED_ATO = "LOCKED_ATO"
    CLOSED = "CLOSED"


class CardBrand(StrEnum):
    """Payment network and card tier credentials."""

    VISA_SIGNATURE = "VISA_SIGNATURE"
    VISA_INFINITE = "VISA_INFINITE"
    MASTERCARD_WORLD_ELITE = "MASTERCARD_WORLD_ELITE"
    AMEX_PLATINUM = "AMEX_PLATINUM"


class CardStatus(StrEnum):
    """Card processing network token authorization status."""

    ACTIVE = "ACTIVE"
    CHALLENGED_3DS = "CHALLENGED_3DS"
    SUSPENDED = "SUSPENDED"
    LOCKED_ATO = "LOCKED_ATO"


class KycStatus(StrEnum):
    """Customer identity verification level."""

    TIER_1_BASIC = "TIER_1_BASIC"
    TIER_2_ID_VERIFIED = "TIER_2_ID_VERIFIED"
    TIER_3_PASSPORT_VERIFIED = "TIER_3_PASSPORT_VERIFIED"


class CustomerRiskTier(StrEnum):
    """Institutional BSA/AML customer risk rating."""

    LOW = "LOW"
    STANDARD = "STANDARD"
    HIGH_RISK = "HIGH_RISK"
    EDD_MONITORED = "EDD_MONITORED"


class CustomerProfile(BaseModel):
    """Verified retail banking customer identity and residential anchor."""

    model_config = ConfigDict(frozen=True)

    user_id: str = Field(pattern=r"^USR_[A-Z0-9]{2,32}$", description="Canonical customer ID")
    full_name: str = Field(min_length=2, max_length=100, description="Legal full name")
    email: str = Field(description="Primary verified email address")
    phone: str = Field(description="E.164 phone number for 3DS OTP delivery")
    residential_address: str = Field(description="Verified physical street address")
    city: str = Field(description="City of residence")
    state: str = Field(description="US State or administrative division")
    postal_code: str = Field(description="Postal/ZIP code")
    country: str = Field(default="US", pattern=r"^[A-Z]{2}$", description="ISO country code")
    home_latitude: float = Field(ge=-90.0, le=90.0, description="Home GPS latitude")
    home_longitude: float = Field(ge=-180.0, le=180.0, description="Home GPS longitude")
    kyc_status: KycStatus = Field(default=KycStatus.TIER_3_PASSPORT_VERIFIED)
    credit_score: int = Field(ge=300, le=850, default=740, description="FICO score")
    risk_tier: CustomerRiskTier = Field(default=CustomerRiskTier.LOW)
    account_opened_at: datetime = Field(description="Banking relationship inception date")


class BankAccount(BaseModel):
    """Deposit or credit line account holding liquid funds."""

    model_config = ConfigDict(frozen=False)

    account_number: str = Field(description="Masked IBAN or DDA account number")
    user_id: str = Field(pattern=r"^USR_[A-Z0-9]{2,32}$")
    routing_number: str = Field(description="ABA routing transit number")
    account_type: AccountType = Field(default=AccountType.CHECKING)
    current_balance: Decimal = Field(decimal_places=2, description="Ledger balance")
    available_balance: Decimal = Field(decimal_places=2, description="Settled available balance")
    currency: str = Field(default="USD", pattern=r"^[A-Z]{3}$")
    status: AccountStatus = Field(default=AccountStatus.ACTIVE)


class PaymentCard(BaseModel):
    """Payment credential linked to a customer deposit account."""

    model_config = ConfigDict(frozen=False)

    card_token: str = Field(description="Network payment token")
    user_id: str = Field(pattern=r"^USR_[A-Z0-9]{2,32}$")
    account_number: str = Field(description="Associated deposit account")
    masked_pan: str = Field(description="PCI-DSS masked primary account number")
    card_brand: CardBrand = Field(default=CardBrand.VISA_SIGNATURE)
    expiry_date: str = Field(pattern=r"^[0-1][0-9]/[2-3][0-9]$", description="MM/YY")
    daily_spend_limit: Decimal = Field(default=Decimal("5000.00"), decimal_places=2)
    status: CardStatus = Field(default=CardStatus.ACTIVE)


class DeviceFootprint(BaseModel):
    """Registered digital identity and hardware profile."""

    model_config = ConfigDict(frozen=True)

    device_id: str = Field(min_length=3, max_length=64, description="Device UUID hash")
    user_id: str = Field(pattern=r"^USR_[A-Z0-9]{2,32}$")
    device_model: str = Field(description="Hardware model name")
    user_agent: str = Field(description="Authentic client browser/OS user agent")
    trusted_ip_subnet: str = Field(description="Customer residential CIDR prefix (e.g. 73.189.42.0/24)")
    isp_name: str = Field(description="Residential internet service provider")
    biometric_enrolled: bool = Field(default=True, description="True if FaceID/TouchID is enabled")


class BankingCustomerRecord(BaseModel):
    """Unified composite banking customer graph record."""

    model_config = ConfigDict(frozen=False)

    profile: CustomerProfile
    accounts: list[BankAccount] = Field(default_factory=list)
    cards: list[PaymentCard] = Field(default_factory=list)
    devices: list[DeviceFootprint] = Field(default_factory=list)
    baseline: UserBaseline
