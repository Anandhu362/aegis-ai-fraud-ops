"""Feature vector and statistical signal schemas computed during enrichment."""

from pydantic import BaseModel, ConfigDict, Field


class UserBaseline(BaseModel):
    """Historical behavioural baseline for the account."""

    model_config = ConfigDict(frozen=True)

    avg_amount: float = Field(default=0.0, description="90-day mean transaction amount")
    std_amount: float = Field(default=0.0, description="90-day standard deviation")
    median_amount: float = Field(default=0.0, description="90-day median amount")
    p95_amount: float = Field(default=0.0, description="90-day 95th percentile amount")
    tx_count_90d: int = Field(default=0, description="Number of settled transactions in 90 days")
    known_categories: list[str] = Field(
        default_factory=list, description="Historical merchant categories"
    )
    known_countries: list[str] = Field(default_factory=list, description="Historical country codes")
    known_devices: list[str] = Field(
        default_factory=list, description="Historical device identifiers"
    )
    cold_start: bool = Field(
        default=False, description="True if insufficient history (<5 transactions)"
    )
    as_of: str | None = Field(default=None, description="Baseline computation date (YYYY-MM-DD)")


class MonetaryAnomaly(BaseModel):
    """Statistical deviation of transaction amount against baseline."""

    model_config = ConfigDict(frozen=True)

    z_score: float = Field(
        default=0.0, description="Standard deviations from mean (clipped [-10, 10])"
    )
    ratio_to_p95: float = Field(
        default=0.0, description="Ratio of amount to baseline 95th percentile"
    )
    ratio_to_median: float = Field(default=0.0, description="Ratio of amount to baseline median")
    is_anomalous: bool = Field(
        default=False, description="True if z_score > 3.0 or ratio_to_p95 > 2.5"
    )


class CategoryCheck(BaseModel):
    """Merchant category risk and novelty."""

    model_config = ConfigDict(frozen=True)

    is_novel: bool = Field(default=False, description="True if category never observed for user")
    is_high_risk: bool = Field(
        default=False, description="True if category is in high-risk list (crypto, etc)"
    )


class VelocityStats(BaseModel):
    """Rolling velocity and structuring signals."""

    model_config = ConfigDict(frozen=True)

    count_60s: int = Field(default=0, description="Transactions in last 60 seconds")
    count_15m: int = Field(default=0, description="Transactions in last 15 minutes")
    near_threshold_count_15m: int = Field(
        default=0,
        description="Transactions in $8,000-$9,999 band in last 15 minutes",
    )
    in_structuring_band: bool = Field(
        default=False,
        description="Current transaction is in near-threshold structuring band ($8k-$9.99k)",
    )
    structuring_hit: bool = Field(
        default=False,
        description="Structuring detected (>=2 transactions in structuring band in 15m window)",
    )


class IpReputation(BaseModel):
    """IP intelligence and anonymization signals."""

    model_config = ConfigDict(frozen=True)

    is_tor: bool = Field(default=False, description="True if IP matches known Tor exit node list")
    is_vpn: bool = Field(default=False, description="True if commercial VPN provider detected")
    is_hosting: bool = Field(default=False, description="True if data center or hosting ASN")
    asn: str | None = Field(default=None, description="Autonomous System Number")
    asn_type: str | None = Field(default=None, description="ISP, HOSTING, or BUSINESS")
    abuse_score: int = Field(
        default=0, ge=0, le=100, description="IP abuse confidence score (0-100)"
    )
    country: str | None = Field(default=None, description="IP geolocation country code")
    unknown: bool = Field(default=False, description="True if IP lookup failed or private IP")


class TravelCheck(BaseModel):
    """Geographic travel velocity analysis."""

    model_config = ConfigDict(frozen=True)

    prev_city: str | None = Field(default=None, description="Previous transaction city")
    distance_km: float = Field(
        default=0.0, description="Haversine distance from previous transaction"
    )
    elapsed_min: float = Field(
        default=0.0, description="Elapsed time in minutes since previous transaction"
    )
    speed_kmh: float = Field(default=0.0, description="Required travel speed in km/h")
    impossible: bool = Field(
        default=False,
        description="True if travel speed > 900 km/h over >= 200 km (impossible travel)",
    )
    exempt: bool = Field(
        default=False,
        description="True if both transactions are ECOMMERCE without physical card present",
    )


class DeviceCheck(BaseModel):
    """Device identity and novelty check."""

    model_config = ConfigDict(frozen=True)

    is_new: bool = Field(default=False, description="True if device_id not in user known_devices")


class GeoCheck(BaseModel):
    """IP versus transaction location consistency."""

    model_config = ConfigDict(frozen=True)

    country_mismatch: bool = Field(
        default=False,
        description="True if IP country does not match transaction origin country",
    )


class FeatureVector(BaseModel):
    """Composite enriched feature representation for deterministic & LLM evaluation."""

    model_config = ConfigDict(frozen=True)

    baseline: UserBaseline = Field(default_factory=UserBaseline)
    monetary: MonetaryAnomaly = Field(default_factory=MonetaryAnomaly)
    category: CategoryCheck = Field(default_factory=CategoryCheck)
    velocity: VelocityStats = Field(default_factory=VelocityStats)
    ip: IpReputation = Field(default_factory=IpReputation)
    travel: TravelCheck = Field(default_factory=TravelCheck)
    device: DeviceCheck = Field(default_factory=DeviceCheck)
    geo: GeoCheck = Field(default_factory=GeoCheck)
