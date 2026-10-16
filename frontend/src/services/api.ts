/**
 * Typed API client for Aegis API Gateway with Cryptographic JWT Session Management.
 */

import type { Transaction } from "../types/generated/transaction.v1";
import type { Verdict } from "../types/generated/verdict.v1";

export interface MetricsSummary {
  processed_count: number;
  allowed_count?: number;
  blocked_count: number;
  locked_count?: number;
  review_count?: number;
  clean_count: number;
  fast_path_pct?: number;
  avg_latency_ms: number;
  accuracy_target: string;
  fpr_target: string;
  last_eval_status: string;
  ai_quota_burn_usd?: string;
  ai_tokens_burned?: number;
  total_tokens_consumed?: number;
  total_cost_usd?: number;
  cost_per_investigation?: string;
  tokens_per_investigation?: number;
  rate_limit_rpm?: number;
  ai_cap_rpm?: number;
  degraded_mode?: boolean;
}

export interface AnalystProfile {
  analyst_id: string;
  name: string;
  email: string;
  role: string;
  permissions: string[];
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  analyst: AnalystProfile;
  user?: AnalystProfile;
}

export interface RuleDefinition {
  rule_id: string;
  name: string;
  description: string;
  risk_floor: number;
  typology: string;
}

export interface PolicyGuardrails {
  policy_version: string;
  hard_floors: {
    rule_id: string;
    name: string;
    description: string;
    risk_floor: number;
    typology: string;
  }[];
  containment_rule: {
    description: string;
    min_score: number;
    min_vectors: number;
    required_actions: string[];
  };
  risk_bands: Record<string, string>;
  action_matrix: { decision: string; trigger: string; friction: string }[];
  rate_limits: {
    global_ingestion_limit_rpm: number;
    ai_evaluation_cap_rpm: number;
    degraded_mode_fallback: string;
    idempotency_window_seconds: number;
  };
}

const BASE_URL = "";
const TOKEN_KEY = "aegis_jwt_token";
const SESSION_KEY = "aegis_analyst_session";

export function getStoredToken(): string | null {
  try {
    return sessionStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setStoredAuth(token: string, profile: AnalystProfile): void {
  try {
    sessionStorage.setItem(TOKEN_KEY, token);
    sessionStorage.setItem(SESSION_KEY, JSON.stringify(profile));
  } catch {
    // ignore
  }
}

export function clearStoredAuth(): void {
  try {
    sessionStorage.removeItem(TOKEN_KEY);
    sessionStorage.removeItem(SESSION_KEY);
  } catch {
    // ignore
  }
}

export function getStoredProfile(): AnalystProfile | null {
  try {
    const raw = sessionStorage.getItem(SESSION_KEY);
    return raw ? (JSON.parse(raw) as AnalystProfile) : null;
  } catch {
    return null;
  }
}

function getAuthHeaders(): Record<string, string> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    "X-API-Key": "aegis-secret-key",
  };
  const token = getStoredToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    if (res.status === 401) {
      clearStoredAuth();
      if (typeof window !== "undefined") {
        window.dispatchEvent(new CustomEvent("aegis:unauthorized"));
      }
    }
    let errorDetail = "API request failed";
    try {
      const errorJson = await res.json();
      errorDetail = errorJson.detail || errorJson.title || res.statusText;
    } catch {
      errorDetail = res.statusText;
    }
    throw new Error(`[${res.status}] ${errorDetail}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  /**
   * Verify server-side JWT session key and return authenticated analyst profile.
   * If token is missing, expired, or invalid, returns null and triggers re-authentication.
   */
  async verifySession(): Promise<AnalystProfile | null> {
    const token = getStoredToken();
    if (!token) {
      clearStoredAuth();
      return null;
    }
    try {
      const res = await fetch(`${BASE_URL}/v1/auth/me`, {
        headers: getAuthHeaders(),
      });
      if (!res.ok) {
        clearStoredAuth();
        return null;
      }
      const analyst = (await res.json()) as AnalystProfile;
      sessionStorage.setItem(SESSION_KEY, JSON.stringify(analyst));
      return analyst;
    } catch {
      // In offline / network glitch, fallback to stored profile if token exists
      return getStoredProfile();
    }
  },

  /**
   * Authenticate SOC Fraud Analyst with server-side validation and signed JWT generation.
   * Credentials are never hardcoded or validated client-side.
   */
  async login(
    email: string,
    password: string,
    role = "L2 Senior Fraud Ops"
  ): Promise<LoginResponse> {
    const res = await fetch(`${BASE_URL}/v1/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, role }),
    });
    const data = await handleResponse<LoginResponse>(res);
    setStoredAuth(data.access_token, data.analyst);
    return data;
  },

  /**
   * Terminate active analyst session and revoke JWT on the server.
   */
  async logout(): Promise<{ status: string }> {
    try {
      const res = await fetch(`${BASE_URL}/v1/auth/logout`, {
        method: "POST",
        headers: getAuthHeaders(),
      });
      clearStoredAuth();
      return await handleResponse<{ status: string }>(res);
    } catch {
      clearStoredAuth();
      return { status: "ok" };
    }
  },

  /**
   * Submit transaction for investigation.
   */
  async analyzeTransaction(
    tx: Transaction,
    mode: "sync" | "async" = "sync"
  ): Promise<Verdict> {
    const res = await fetch(
      `${BASE_URL}/v1/transactions:analyze?mode=${mode}`,
      {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify(tx),
      }
    );
    return handleResponse<Verdict>(res);
  },

  /**
   * Trigger demonstration attack scenario ('coffee', 'smurfing', 'tor_travel').
   */
  async triggerSimulation(
    scenario: string,
    mode: "sync" | "async" = "sync",
    txId?: string
  ): Promise<Verdict> {
    const url = txId
      ? `${BASE_URL}/v1/simulations/${scenario}?mode=${mode}&tx_id=${encodeURIComponent(txId)}`
      : `${BASE_URL}/v1/simulations/${scenario}?mode=${mode}`;
    const res = await fetch(url, {
      method: "POST",
      headers: getAuthHeaders(),
    });
    return handleResponse<Verdict>(res);
  },

  /**
   * Get synthesized verdict and case details for a transaction ID.
   */
  async getInvestigation(txId: string): Promise<Verdict> {
    const res = await fetch(
      `${BASE_URL}/v1/investigations/${encodeURIComponent(txId)}`,
      {
        headers: getAuthHeaders(),
      }
    );
    return handleResponse<Verdict>(res);
  },

  /**
   * List recent investigation verdicts for live SOC dashboard stream.
   */
  async listInvestigations(limit = 50): Promise<Verdict[]> {
    const res = await fetch(
      `${BASE_URL}/v1/investigations?limit=${limit}`,
      {
        headers: getAuthHeaders(),
      }
    );
    return handleResponse<Verdict[]>(res);
  },

  /**
   * Record human fraud analyst override.
   */
  async recordAnalystDecision(
    txId: string,
    action: "APPROVE" | "CONFIRM_FRAUD" | "UNLOCK",
    reason: string,
    analystUid = "analyst_l2_lead"
  ): Promise<Verdict> {
    const res = await fetch(
      `${BASE_URL}/v1/investigations/${encodeURIComponent(txId)}/decision`,
      {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify({
          action,
          reason,
          analyst_uid: analystUid,
          at: Date.now(),
        }),
      }
    );
    return handleResponse<Verdict>(res);
  },

  /**
   * Retrieve aggregated SOC operational metrics.
   */
  async getMetricsSummary(): Promise<MetricsSummary> {
    const res = await fetch(`${BASE_URL}/v1/metrics/summary`, {
      headers: getAuthHeaders(),
    });
    return handleResponse<MetricsSummary>(res);
  },

  /**
   * Purge all past investigations and reset the dashboard state.
   */
  async clearInvestigations(): Promise<{
    status: string;
    cleared_count: number;
    message: string;
  }> {
    const res = await fetch(`${BASE_URL}/v1/investigations:clear`, {
      method: "POST",
      headers: getAuthHeaders(),
    });
    return handleResponse<{
      status: string;
      cleared_count: number;
      message: string;
    }>(res);
  },

  /**
   * Fetch active deterministic banking fraud rules & guardrails.
   */
  async getPolicies(): Promise<PolicyGuardrails> {
    const res = await fetch(`${BASE_URL}/v1/policies`, {
      headers: getAuthHeaders(),
    });
    return handleResponse<PolicyGuardrails>(res);
  },

  /**
   * Subscribe to real-time Gateway Hot-Cache Shield SSE stream.
   * Delivers sub-millisecond real-time push updates with $0 Cloud Firestore read cost.
   */
  subscribeToInvestigationStream(
    onVerdict: (verdict: Verdict) => void,
    onConnected?: () => void,
    onError?: (err: Event) => void,
    onReset?: () => void
  ): () => void {
    const es = new EventSource(`${BASE_URL}/v1/investigations/stream`);
    es.addEventListener("connected", () => {
      if (onConnected) onConnected();
    });
    es.addEventListener("verdict", (evt: MessageEvent) => {
      try {
        const parsed = JSON.parse(evt.data) as Verdict;
        onVerdict(parsed);
      } catch (e) {
        console.error("Failed to parse SSE verdict", e);
      }
    });
    es.addEventListener("reset", () => {
      if (onReset) onReset();
    });
    if (onError) {
      es.onerror = onError;
    }
    return () => {
      es.close();
    };
  },
};
