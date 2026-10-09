"""Transaction and geographic location schemas."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, IPvAnyAddress

from aegis_common.schemas.enums import Channel, MerchantCategory


class Location(BaseModel):
    """Geographic coordinate and administrative location."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    latitude: float = Field(ge=-90.0, le=90.0, description="Latitude in decimal degrees [-90, 90]")
    longitude: float = Field(
        ge=-180.0, le=180.0, description="Longitude in decimal degrees [-180, 180]"
    )
    city: str = Field(min_length=1, max_length=80, description="City name")
    country: str = Field(pattern=r"^[A-Z]{2}$", description="ISO-3166-1 alpha-2 country code")


class Transaction(BaseModel):
    """Incoming payment transaction payload."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    tx_id: str = Field(pattern=r"^TX_[A-Z0-9]{4,32}$", description="Unique transaction ID")
    user_id: str = Field(pattern=r"^USR_[A-Z0-9]{2,32}$", description="Customer/account ID")
    timestamp: datetime = Field(description="RFC 3339 UTC timestamp")
    amount: Decimal = Field(
        gt=0, le=1_000_000, decimal_places=2, description="Monetary value (>0, <=1M, 2dp)"
    )
    currency: str = Field(pattern=r"^[A-Z]{3}$", description="ISO-4217 3-letter currency code")
    merchant: str = Field(min_length=1, max_length=120, description="Untrusted merchant name")
    merchant_category: MerchantCategory = Field(description="Categorical merchant classification")
    channel: Channel = Field(default=Channel.ECOMMERCE, description="Transaction channel")
    device_id: str = Field(
        min_length=1, max_length=64, description="Client device hardware/browser hash"
    )
    ip_address: IPvAnyAddress | None = Field(
        default=None, description="Client IPv4 or IPv6 address"
    )
    location: Location = Field(description="Transaction origin geolocation")
