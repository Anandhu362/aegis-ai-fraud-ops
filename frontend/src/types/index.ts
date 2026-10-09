/**
 * Core frontend type exports.
 */

export interface CaseSummary {
  tx_id: string;
  user_id: string;
  amount: number;
  currency: string;
  merchant: string;
  threat_score: number;
  risk_level: "LOW" | "ELEVATED" | "HIGH" | "CRITICAL";
  decision: "ALLOW" | "REVIEW" | "BLOCK_TX" | "LOCK_ACCOUNT" | "DECLINE_LOCKED";
  status: "QUEUED" | "PROCESSING" | "COMPLETED" | "ACTION_TAKEN" | "FAILED";
  timestamp: number;
}
