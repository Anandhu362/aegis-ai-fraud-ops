import React, { useEffect, useState } from "react";
import {
  ShieldAlert,
  Lock,
  Scale,
  CheckCircle2,
} from "lucide-react";
import { api, type PolicyGuardrails } from "../services/api";

export function PolicyEngineView(): React.JSX.Element {
  const [policies, setPolicies] = useState<PolicyGuardrails | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const data = await api.getPolicies();
        setPolicies(data);
      } catch {
        // Fallback default structure
        setPolicies({
          policy_version: "v1.1",
          hard_floors: [
            {
              rule_id: "H1",
              name: "Tor Exit Node + Impossible Travel",
              description: "Anonymous network node combined with travel velocity exceeding 800 km/h.",
              risk_floor: 90,
              typology: "ACCOUNT_TAKEOVER",
            },
            {
              rule_id: "H2",
              name: "Structuring Velocity Burst",
              description: "Near-threshold payments ($9,000–$9,999) or rapid velocity burst in 60s.",
              risk_floor: 85,
              typology: "SMURFING_STRUCTURING",
            },
            {
              rule_id: "H3",
              name: "High-Risk Category Deviation",
              description: "Novel high-risk merchant (crypto/gambling) deviating from 90-day baseline.",
              risk_floor: 80,
              typology: "HIGH_RISK_MERCHANT",
            },
          ],
          containment_rule: {
            description: "Autonomous customer account freeze is permitted ONLY if Threat Score >= 85 and 2+ distinct vectors match.",
            min_score: 85,
            min_vectors: 2,
            required_actions: ["account_locked", "tx_blocked", "alert_dispatched"],
          },
          risk_bands: {
            LOW: "0 - 29 (Frictionless Fast-Path approval, < 700ms)",
            ELEVATED: "30 - 69 (Step-up authentication / 3DS Challenge or Analyst Review)",
            HIGH: "70 - 84 (Inline transaction block, audit telemetry dispatched)",
            CRITICAL: "85 - 100 (Autonomous account freeze & emergency customer alert)",
          },
          action_matrix: [
            { decision: "ALLOW", trigger: "Score < 30", friction: "Zero Customer Friction" },
            { decision: "CHALLENGE_3DS", trigger: "Score 30-69 or Novel Device", friction: "One-Time Passcode" },
            { decision: "BLOCK_TX", trigger: "Score >= 70 or Velocity Burst", friction: "Transaction Declined" },
            { decision: "LOCK_ACCOUNT", trigger: "Score >= 85 and 2+ Vectors", friction: "Account Frozen" },
          ],
          rate_limits: {
            global_ingestion_limit_rpm: 60,
            ai_evaluation_cap_rpm: 15,
            degraded_mode_fallback: "Pure Deterministic Policy Engine",
            idempotency_window_seconds: 60,
          },
        });
      }
    };
    load();
  }, []);

  return (
    <div className="flex flex-col gap-6">
      {/* Banner */}
      <div className="p-6 rounded-[28px] bg-white border border-[var(--color-border)] shadow-[var(--shadow-card)] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-violet-50 text-violet-800 border border-violet-200 text-xs font-semibold mb-2">
            <ShieldAlert className="w-3.5 h-3.5 text-violet-600" />
            <span>Deterministic Policy Guardrails • v1.1 Active</span>
          </div>
          <h2 className="text-xl sm:text-2xl font-black text-[var(--color-brand-midnight)] tracking-tight">
            Automated Risk Policies & Hard-Floor Guardrails
          </h2>
          <p className="text-xs text-[var(--color-text-secondary)] mt-1 max-w-2xl leading-relaxed">
            Deterministic code establishes facts, LLMs interpret evidence, and deterministic policy controls consequential actions. AI agents cannot lower hard-rule floors or autonomously execute freezes without meeting strict banking containment criteria.
          </p>
        </div>

        <div className="flex items-center gap-2 bg-emerald-50 text-emerald-800 border border-emerald-200 px-4 py-2 rounded-2xl text-xs font-bold font-mono">
          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          <span>Policy Engine Online</span>
        </div>
      </div>

      {/* Grid: Hard Floors & Containment Rules */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Hard Rule Floors */}
        <div className="lg:col-span-2 bg-white rounded-[28px] border border-[var(--color-border)] shadow-[var(--shadow-card)] p-6 flex flex-col gap-4">
          <div className="flex items-center justify-between border-b border-[var(--color-border)] pb-3">
            <div className="flex items-center gap-2">
              <Scale className="w-4 h-4 text-violet-600" />
              <h3 className="text-sm font-bold text-[var(--color-brand-midnight)]">
                Hard-Rule Floors (Deterministic Guarantees)
              </h3>
            </div>
            <span className="text-[10px] font-mono text-slate-500 font-semibold">
              IMMUTABLE POLICY
            </span>
          </div>

          <p className="text-xs text-[var(--color-text-secondary)] leading-relaxed">
            When a verified threat rule triggers, the final threat score is clamped to never drop below the rule floor, preventing model hallucinations from suppressing genuine threats.
          </p>

          <div className="space-y-3 mt-1">
            {policies?.hard_floors.map((rule) => (
              <div
                key={rule.rule_id}
                className="p-4 rounded-2xl bg-[var(--color-surface-subtle)] border border-[var(--color-border)] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3"
              >
                <div className="flex items-start gap-3">
                  <span className="w-8 h-8 rounded-xl bg-[var(--color-brand-midnight)] text-white font-mono font-bold text-xs flex items-center justify-center shrink-0">
                    {rule.rule_id}
                  </span>
                  <div>
                    <div className="text-xs font-bold text-[var(--color-brand-midnight)]">
                      {rule.name}
                    </div>
                    <div className="text-[11px] text-[var(--color-text-secondary)] mt-0.5">
                      {rule.description}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2 self-end sm:self-center shrink-0">
                  <div className="text-right">
                    <div className="text-[10px] font-mono uppercase text-slate-500">Floor Minimum</div>
                    <div className="text-xs font-mono font-black text-rose-700">
                      Score &ge; {rule.risk_floor}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Consequential Actuator Containment Criteria */}
        <div className="bg-white rounded-[28px] border border-[var(--color-border)] shadow-[var(--shadow-card)] p-6 flex flex-col justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 border-b border-[var(--color-border)] pb-3 mb-4">
              <Lock className="w-4 h-4 text-rose-600" />
              <h3 className="text-sm font-bold text-[var(--color-brand-midnight)]">
                Autonomous Containment Guardrail
              </h3>
            </div>

            <div className="p-4 rounded-2xl bg-rose-50/60 border border-rose-200/80 flex flex-col gap-3">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-rose-600 animate-pulse" />
                <span className="text-xs font-bold text-rose-900">
                  Strict Auto-Lock Requirements
                </span>
              </div>
              <p className="text-[11px] text-rose-800 leading-relaxed">
                Autonomous account lockout and card suspension are executed only when:
              </p>
              <ul className="text-[11px] text-rose-900 space-y-1.5 list-disc list-inside font-medium">
                <li>Threat Score is at least <strong>85 / 100</strong></li>
                <li>At least <strong>2 distinct threat vectors</strong> match</li>
                <li>Audit entry is appended to BigQuery</li>
              </ul>
            </div>

            {/* Decision Thresholds */}
            <div className="mt-4 space-y-2">
              <span className="text-[10px] font-mono uppercase text-slate-400 font-bold">
                Action Matrix
              </span>
              {policies?.action_matrix.map((row) => (
                <div
                  key={row.decision}
                  className="flex items-center justify-between p-2.5 rounded-xl bg-[var(--color-surface-subtle)] border border-[var(--color-border)] text-xs font-mono"
                >
                  <span className="font-bold text-[var(--color-brand-midnight)]">{row.decision}</span>
                  <span className="text-[11px] text-slate-600">{row.trigger}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="p-3 rounded-2xl bg-slate-50 border border-slate-200 text-[10px] text-slate-600 font-mono">
            Rate Limiter: {policies?.rate_limits.global_ingestion_limit_rpm} RPM • AI Cap: {policies?.rate_limits.ai_evaluation_cap_rpm} RPM
          </div>
        </div>
      </div>
    </div>
  );
}
