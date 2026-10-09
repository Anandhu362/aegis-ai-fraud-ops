/* eslint-disable */
/**
 * Auto-generated from Aegis Pydantic Schema. Do NOT edit manually.
 */

/**
 * Strict monotonically increasing sequence number (0, 1, 2...)
 */
export type Seq = number;
/**
 * Name of the agent emitting the event
 */
export type Agent = string;
/**
 * Type of event (THOUGHT, TOOL_CALL, TOOL_RESULT, etc.)
 */
export type TelemetryAction = "THOUGHT" | "TOOL_CALL" | "TOOL_RESULT" | "FINDING" | "VERDICT" | "ACTION" | "ERROR";
/**
 * INFO, WARN, or CRITICAL
 */
export type Severity = string;
/**
 * Human-readable terminal log line
 */
export type Message = string;
/**
 * Execution duration of this specific step in ms
 */
export type LatencyMs = number;
/**
 * Epoch timestamp in milliseconds
 */
export type Timestamp = number;

/**
 * An ordered telemetry milestone emitted during agent pipeline execution.
 */
export interface TelemetryEvent {
  seq: Seq;
  agent: Agent;
  action: TelemetryAction;
  severity?: Severity;
  message: Message;
  data?: Data;
  latency_ms?: LatencyMs;
  timestamp: Timestamp;
  [k: string]: unknown;
}
/**
 * Structured payload or tool arguments/result
 */
export interface Data {
  [k: string]: unknown;
}
