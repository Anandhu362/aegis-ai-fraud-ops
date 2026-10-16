import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { api } from "./api";
import type { Verdict } from "../types/generated/verdict.v1";

describe("Aegis API Service", () => {
  const mockVerdict: Verdict = {
    tx_id: "tx-test-01",
    user_id: "usr-01",
    threat_score: 95,
    risk_level: "CRITICAL",
    decision: "LOCK_ACCOUNT",
    rationale: "Impossible travel detected.",
  };

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("triggerSimulation posts to correct simulation endpoint and returns verdict", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
      ok: true,
      json: async () => mockVerdict,
    } as Response);

    const result = await api.triggerSimulation("tor_travel", "sync");
    expect(fetchSpy).toHaveBeenCalledWith("/v1/simulations/tor_travel?mode=sync", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
    expect(result.tx_id).toBe("tx-test-01");
    expect(result.decision).toBe("LOCK_ACCOUNT");
  });

  it("recordAnalystDecision sends analyst override payload", async () => {
    const updatedVerdict: Verdict = {
      ...mockVerdict,
      analyst_decision: {
        action: "UNLOCK",
        reason: "Customer verified out-of-band",
        analyst_uid: "analyst_l2_lead",
        at: 1700000000000,
      },
    };

    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
      ok: true,
      json: async () => updatedVerdict,
    } as Response);

    const result = await api.recordAnalystDecision("tx-test-01", "UNLOCK", "Customer verified out-of-band");
    expect(fetchSpy).toHaveBeenCalled();
    expect(result.analyst_decision?.action).toBe("UNLOCK");
  });

  it("handles non-ok API responses by throwing descriptive error", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
      ok: false,
      status: 404,
      statusText: "Not Found",
      json: async () => ({ detail: "Investigation case not found" }),
    } as Response);

    await expect(api.getInvestigation("tx-nonexistent")).rejects.toThrow(
      "[404] Investigation case not found"
    );
  });
});
