/* eslint-disable */
/**
 * Auto-generated from Aegis Pydantic Schema. Do NOT edit manually.
 */

/**
 * 90-day mean transaction amount
 */
export type AvgAmount = number;
/**
 * 90-day standard deviation
 */
export type StdAmount = number;
/**
 * 90-day median amount
 */
export type MedianAmount = number;
/**
 * 90-day 95th percentile amount
 */
export type P95Amount = number;
/**
 * Number of settled transactions in 90 days
 */
export type TxCount90D = number;
/**
 * Historical merchant categories
 */
export type KnownCategories = string[];
/**
 * Historical country codes
 */
export type KnownCountries = string[];
/**
 * Historical device identifiers
 */
export type KnownDevices = string[];
/**
 * True if insufficient history (<5 transactions)
 */
export type ColdStart = boolean;
/**
 * Baseline computation date (YYYY-MM-DD)
 */
export type AsOf = string | null;
/**
 * Standard deviations from mean (clipped [-10, 10])
 */
export type ZScore = number;
/**
 * Ratio of amount to baseline 95th percentile
 */
export type RatioToP95 = number;
/**
 * Ratio of amount to baseline median
 */
export type RatioToMedian = number;
/**
 * True if z_score > 3.0 or ratio_to_p95 > 2.5
 */
export type IsAnomalous = boolean;
/**
 * True if category never observed for user
 */
export type IsNovel = boolean;
/**
 * True if category is in high-risk list (crypto, etc)
 */
export type IsHighRisk = boolean;
/**
 * Transactions in last 60 seconds
 */
export type Count60S = number;
/**
 * Transactions in last 15 minutes
 */
export type Count15M = number;
/**
 * Transactions in $8,000–$9,999 band in last 15 minutes
 */
export type NearThresholdCount15M = number;
/**
 * Current transaction is in near-threshold structuring band ($8k-$9.99k)
 */
export type InStructuringBand = boolean;
/**
 * Structuring detected (>=2 transactions in structuring band in 15m window)
 */
export type StructuringHit = boolean;
/**
 * True if IP matches known Tor exit node list
 */
export type IsTor = boolean;
/**
 * True if commercial VPN provider detected
 */
export type IsVpn = boolean;
/**
 * True if data center or hosting ASN
 */
export type IsHosting = boolean;
/**
 * Autonomous System Number
 */
export type Asn = string | null;
/**
 * ISP, HOSTING, or BUSINESS
 */
export type AsnType = string | null;
/**
 * IP abuse confidence score (0-100)
 */
export type AbuseScore = number;
/**
 * IP geolocation country code
 */
export type Country = string | null;
/**
 * True if IP lookup failed or private IP
 */
export type Unknown = boolean;
/**
 * Previous transaction city
 */
export type PrevCity = string | null;
/**
 * Haversine distance from previous transaction
 */
export type DistanceKm = number;
/**
 * Elapsed time in minutes since previous transaction
 */
export type ElapsedMin = number;
/**
 * Required travel speed in km/h
 */
export type SpeedKmh = number;
/**
 * True if travel speed > 900 km/h over >= 200 km (impossible travel)
 */
export type Impossible = boolean;
/**
 * True if both transactions are ECOMMERCE without physical card present
 */
export type Exempt = boolean;
/**
 * True if device_id not in user known_devices
 */
export type IsNew = boolean;
/**
 * True if IP country does not match transaction origin country
 */
export type CountryMismatch = boolean;

/**
 * Composite enriched feature representation for deterministic & LLM evaluation.
 */
export interface FeatureVector {
  baseline?: UserBaseline;
  monetary?: MonetaryAnomaly;
  category?: CategoryCheck;
  velocity?: VelocityStats;
  ip?: IpReputation;
  travel?: TravelCheck;
  device?: DeviceCheck;
  geo?: GeoCheck;
  [k: string]: unknown;
}
/**
 * Historical behavioural baseline for the account.
 */
export interface UserBaseline {
  avg_amount?: AvgAmount;
  std_amount?: StdAmount;
  median_amount?: MedianAmount;
  p95_amount?: P95Amount;
  tx_count_90d?: TxCount90D;
  known_categories?: KnownCategories;
  known_countries?: KnownCountries;
  known_devices?: KnownDevices;
  cold_start?: ColdStart;
  as_of?: AsOf;
  [k: string]: unknown;
}
/**
 * Statistical deviation of transaction amount against baseline.
 */
export interface MonetaryAnomaly {
  z_score?: ZScore;
  ratio_to_p95?: RatioToP95;
  ratio_to_median?: RatioToMedian;
  is_anomalous?: IsAnomalous;
  [k: string]: unknown;
}
/**
 * Merchant category risk and novelty.
 */
export interface CategoryCheck {
  is_novel?: IsNovel;
  is_high_risk?: IsHighRisk;
  [k: string]: unknown;
}
/**
 * Rolling velocity and structuring signals.
 */
export interface VelocityStats {
  count_60s?: Count60S;
  count_15m?: Count15M;
  near_threshold_count_15m?: NearThresholdCount15M;
  in_structuring_band?: InStructuringBand;
  structuring_hit?: StructuringHit;
  [k: string]: unknown;
}
/**
 * IP intelligence and anonymization signals.
 */
export interface IpReputation {
  is_tor?: IsTor;
  is_vpn?: IsVpn;
  is_hosting?: IsHosting;
  asn?: Asn;
  asn_type?: AsnType;
  abuse_score?: AbuseScore;
  country?: Country;
  unknown?: Unknown;
  [k: string]: unknown;
}
/**
 * Geographic travel velocity analysis.
 */
export interface TravelCheck {
  prev_city?: PrevCity;
  distance_km?: DistanceKm;
  elapsed_min?: ElapsedMin;
  speed_kmh?: SpeedKmh;
  impossible?: Impossible;
  exempt?: Exempt;
  [k: string]: unknown;
}
/**
 * Device identity and novelty check.
 */
export interface DeviceCheck {
  is_new?: IsNew;
  [k: string]: unknown;
}
/**
 * IP versus transaction location consistency.
 */
export interface GeoCheck {
  country_mismatch?: CountryMismatch;
  [k: string]: unknown;
}
