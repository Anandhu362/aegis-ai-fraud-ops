/* eslint-disable */
/**
 * Auto-generated from Aegis Pydantic Schema. Do NOT edit manually.
 */

/**
 * Unique transaction ID
 */
export type TxId = string;
/**
 * Customer/account ID
 */
export type UserId = string;
/**
 * RFC 3339 UTC timestamp
 */
export type Timestamp = string;
/**
 * Monetary value (>0, <=1M, 2dp)
 */
export type Amount = number | string;
/**
 * ISO-4217 3-letter currency code
 */
export type Currency = string;
/**
 * Untrusted merchant name
 */
export type Merchant = string;
/**
 * Categorical merchant classification
 */
export type MerchantCategory =
  | "coffee_shop"
  | "grocery"
  | "restaurant"
  | "fuel"
  | "retail"
  | "electronics"
  | "travel"
  | "utilities"
  | "pharmacy"
  | "entertainment"
  | "cryptocurrency_brokerage"
  | "gambling"
  | "money_transfer"
  | "gift_cards"
  | "wire_transfer";
/**
 * Transaction channel
 */
export type Channel = "CARD_PRESENT" | "ECOMMERCE" | "TRANSFER" | "ATM";
/**
 * Client device hardware/browser hash
 */
export type DeviceId = string;
/**
 * Client IPv4 or IPv6 address
 */
export type IpAddress = string | null;
/**
 * Latitude in decimal degrees [-90, 90]
 */
export type Latitude = number;
/**
 * Longitude in decimal degrees [-180, 180]
 */
export type Longitude = number;
/**
 * City name
 */
export type City = string;
/**
 * ISO-3166-1 alpha-2 country code
 */
export type Country = string;

/**
 * Incoming payment transaction payload.
 */
export interface Transaction {
  tx_id: TxId;
  user_id: UserId;
  timestamp: Timestamp;
  amount: Amount;
  currency: Currency;
  merchant: Merchant;
  merchant_category: MerchantCategory;
  channel?: Channel;
  device_id: DeviceId;
  ip_address?: IpAddress;
  location: Location;
}
/**
 * Transaction origin geolocation
 */
export interface Location {
  latitude: Latitude;
  longitude: Longitude;
  city: City;
  country: Country;
}
