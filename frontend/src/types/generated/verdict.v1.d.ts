/* eslint-disable */
/**
 * Auto-generated from Aegis Pydantic Schema. Do NOT edit manually.
 */

/**
 * Transaction identifier
 */
export type TxId = string;
/**
 * Customer identifier
 */
export type UserId = string;
/**
 * Investigation lifecycle state
 */
export type InvestigationStatus = "QUEUED" | "PROCESSING" | "COMPLETED" | "ACTION_TAKEN" | "FAILED";
/**
 * Final 0-100 composite threat score
 */
export type ThreatScore = number;
/**
 * Categorical risk band
 */
export type RiskLevel = "LOW" | "ELEVATED" | "HIGH" | "CRITICAL";
/**
 * Automated policy decision
 */
export type Decision = "ALLOW" | "REVIEW" | "BLOCK_TX" | "LOCK_ACCOUNT" | "DECLINE_LOCKED";
/**
 * True if automated containment was required
 */
export type ShouldActuate = boolean;
/**
 * Classified fraud pattern
 */
export type Typology =
  "NONE" | "ACCOUNT_TAKEOVER" | "STRUCTURING" | "CREDENTIAL_STUFFING" | "CARD_TESTING" | "MERCHANT_DEVIATION" | "OTHER";
/**
 * Evidence-backed human readable explanation
 */
export type Rationale = string;
/**
 * Pointers to validated signals used in decision
 */
export type CitedEvidence = string[];
/**
 * Deterministic base score from weighted signals
 */
export type Base = number;
/**
 * Highest triggered hard-rule risk floor
 */
export type Floor = number;
/**
 * Bounded orchestrator adjustment [-10, +10]
 */
export type LlmAdjustment = number;
/**
 * IDs of hard rules triggered (e.g. H1)
 */
export type Rules = string[];
/**
 * Core banking account lockout status
 */
export type AccountLocked = boolean;
/**
 * Transaction blocked status
 */
export type TxBlocked = boolean;
/**
 * Customer alert dispatched
 */
export type AlertDispatched = boolean;
/**
 * Channel used for security alert
 */
export type DispatchChannel = string;
/**
 * True if lockout occurred before orchestrator verdict via early containment
 */
export type EarlyContainment = boolean;
/**
 * Sanitized feature snapshot
 */
export type FeaturesSnapshot = {
  [k: string]: unknown;
} | null;
/**
 * High-level narrative of the fraud event
 */
export type ExecutiveSummary = string;
/**
 * Reconstructed event timeline
 */
export type Chronology = string[];
/**
 * Analyst recommendation
 */
export type RecommendedAction = string;
/**
 * Agent confidence in review
 */
export type ConfidenceScore = number;
/**
 * APPROVE | CONFIRM_FRAUD | UNLOCK
 */
export type Action = string;
/**
 * Analyst rationale
 */
export type Reason = string;
/**
 * Analyst user identifier
 */
export type AnalystUid = string;
/**
 * Timestamp of action in epoch milliseconds
 */
export type At = number;
/**
 * True if fallback path was used due to model failure
 */
export type Degraded = boolean;
/**
 * risk_policy.yaml semantic version
 */
export type Policy = string;
/**
 * Total pipeline latency in ms
 */
export type Total = number;
/**
 * Deterministic enrichment latency in ms
 */
export type Enrichment = number;
/**
 * Parallel specialists latency in ms
 */
export type Specialists = number;
/**
 * Orchestrator synthesis latency in ms
 */
export type Orchestrator1 = number;
/**
 * Policy execution and actuation latency in ms
 */
export type Policy1 = number;
/**
 * Pipeline start timestamp (epoch ms)
 */
export type StartedAt = number | null;
/**
 * Pipeline completion timestamp (epoch ms)
 */
export type CompletedAt = number | null;

/**
 * Final, explainable investigation verdict and risk assessment.
 */
export interface Verdict {
  tx_id: TxId;
  user_id: UserId;
  status?: InvestigationStatus;
  threat_score: ThreatScore;
  risk_level: RiskLevel;
  decision: Decision;
  should_actuate?: ShouldActuate;
  typology?: Typology;
  rationale: Rationale;
  cited_evidence?: CitedEvidence;
  /**
   * Detailed score decomposition
   */
  score_breakdown?: ScoreBreakdown | null;
  /**
   * Actions executed by actuator
   */
  actuator_action?: ActuatorAction | null;
  features_snapshot?: FeaturesSnapshot;
  /**
   * Asynchronous deep review
   */
  deep_review?: CaseNarrative | null;
  /**
   * Human analyst override
   */
  analyst_decision?: AnalystDecision | null;
  degraded?: Degraded;
  /**
   * Model and policy version metadata
   */
  versions?: ModelVersions | null;
  latency_ms?: LatencyBreakdown;
  started_at?: StartedAt;
  completed_at?: CompletedAt;
  [k: string]: unknown;
}
/**
 * Detailed trace of deterministic base score, hard floors, and LLM adjustment.
 */
export interface ScoreBreakdown {
  base: Base;
  floor: Floor;
  llm_adjustment: LlmAdjustment;
  signals?: Signals;
  rules?: Rules;
  [k: string]: unknown;
}
/**
 * Points awarded per signal ID
 */
export interface Signals {
  [k: string]: number;
}
/**
 * Actions executed or requested by the deterministic PolicyAgent.
 */
export interface ActuatorAction {
  account_locked?: AccountLocked;
  tx_blocked?: TxBlocked;
  alert_dispatched?: AlertDispatched;
  dispatch_channel?: DispatchChannel;
  early_containment?: EarlyContainment;
  [k: string]: unknown;
}
/**
 * Asynchronous deep review narrative generated by Gemini Pro.
 */
export interface CaseNarrative {
  executive_summary: ExecutiveSummary;
  chronology?: Chronology;
  recommended_action: RecommendedAction;
  confidence_score: ConfidenceScore;
  [k: string]: unknown;
}
/**
 * Manual review decision recorded by a human fraud analyst.
 */
export interface AnalystDecision {
  action: Action;
  reason: Reason;
  analyst_uid: AnalystUid;
  at: At;
  [k: string]: unknown;
}
/**
 * Version tracking of active prompts and risk policies.
 */
export interface ModelVersions {
  policy?: Policy;
  orchestrator?: Orchestrator;
  specialist?: Specialist;
  [k: string]: unknown;
}
/**
 * Orchestrator model & prompt version
 */
export interface Orchestrator {
  [k: string]: string;
}
/**
 * Specialist model & prompt version
 */
export interface Specialist {
  [k: string]: string;
}
/**
 * Latency breakdown
 */
export interface LatencyBreakdown {
  total?: Total;
  enrichment?: Enrichment;
  specialists?: Specialists;
  orchestrator?: Orchestrator1;
  policy?: Policy1;
  [k: string]: unknown;
}
