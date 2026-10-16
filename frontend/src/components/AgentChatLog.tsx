import React from "react";
import { Cpu, Shield, ShieldCheck, Terminal } from "lucide-react";
import type { Verdict } from "../types/generated/verdict.v1";

interface AgentChatLogProps {
  verdict: Verdict | null;
}

export function AgentChatLog({ verdict }: AgentChatLogProps): React.JSX.Element {
  if (!verdict) {
    return (
      <div className="p-8 text-center text-xs text-[var(--color-text-muted)] bg-[var(--color-surface-subtle)] rounded-2xl border border-[var(--color-border)]">
        No case selected. Select an investigation from the feed to view real-time agent telemetry.
      </div>
    );
  }

  const breakdown = verdict.score_breakdown;
  const signals = breakdown?.signals ?? {};
  const rules = breakdown?.rules ?? [];
  const adjustment = breakdown?.llm_adjustment ?? 0;
  const actuator = verdict.actuator_action;

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <span className="text-xs font-bold uppercase tracking-wider text-[var(--color-text-secondary)] flex items-center gap-1.5 font-mono">
          <Terminal className="w-3.5 h-3.5 text-violet-600" />
          Multi-Vector Investigation Telemetry
        </span>
        <span className="text-[10px] font-mono text-[var(--color-text-muted)]">
          Case Ref: {verdict.tx_id}
        </span>
      </div>

      <div className="space-y-3 font-sans">
        {/* Step 1: Intake & Baseline Verification */}
        <div className="p-4 rounded-2xl bg-[var(--color-surface-subtle)] border border-[var(--color-border)]">
          <div className="flex items-center justify-between mb-1.5">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-cyan-500" />
              <span className="text-xs font-bold text-[var(--color-brand-midnight)]">
                Account History & Baseline Verification
              </span>
            </div>
            <span className="text-[10px] font-mono text-[var(--color-text-muted)]">Phase 1</span>
          </div>
          <p className="text-xs text-[var(--color-text-secondary)] leading-relaxed">
            Verified transaction against customer's 90-day spending patterns, typical locations, and network identity. Baseline risk score: <strong>{breakdown?.base ?? 0}</strong>.
          </p>
          {Object.keys(signals).length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1.5">
              {Object.entries(signals).map(([sigKey, points]) => (
                <span
                  key={sigKey}
                  className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-white text-slate-700 border border-slate-200"
                >
                  {sigKey} (+{points})
                </span>
              ))}
            </div>
          )}
        </div>


        {/* Step 2: Parallel Specialists (Behavioral & Threat Intel) */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {/* Behavioral Specialist */}
          <div className="p-4 rounded-2xl bg-[var(--color-surface-subtle)] border border-[var(--color-border)] flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-1.5">
                  <Cpu className="w-3.5 h-3.5 text-cyan-600" />
                  <span className="text-xs font-bold text-[var(--color-brand-midnight)]">
                    Spending Behavior Analysis
                  </span>
                </div>
                <span className="text-[10px] font-mono text-cyan-700 font-semibold">Behavioral Vector</span>
              </div>
              <p className="text-[11px] text-[var(--color-text-secondary)] leading-relaxed">
                {verdict.decision === "ALLOW"
                  ? "Spending amount and merchant strictly align with customer's historical habit. Zero velocity burst detected."
                  : `Analyzed monetary anomaly and category deviation for pattern: ${verdict.typology}.`}
              </p>
            </div>
          </div>

          {/* Threat Intel Specialist */}
          <div className="p-4 rounded-2xl bg-[var(--color-surface-subtle)] border border-[var(--color-border)] flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-1.5">
                  <Shield className="w-3.5 h-3.5 text-rose-600" />
                  <span className="text-xs font-bold text-[var(--color-brand-midnight)]">
                    Network & Device Security
                  </span>
                </div>
                <span className="text-[10px] font-mono text-rose-700 font-semibold">Network Vector</span>
              </div>
              <p className="text-[11px] text-[var(--color-text-secondary)] leading-relaxed">
                {rules.includes("H1")
                  ? "Identified untrusted network node and impossible travel velocity exceeding 800 km/h. High-risk location anomaly confirmed."
                  : "IP network safety evaluated. Registered customer device and geographic location confirmed."}
              </p>
            </div>
          </div>
        </div>

        {/* Step 3: Orchestrator Synthesis */}
        <div className="p-4 rounded-2xl bg-white border-2 border-violet-100 shadow-xs">
          <div className="flex items-center justify-between mb-1.5">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-3.5 h-3.5 text-violet-600" />
              <span className="text-xs font-bold text-[var(--color-brand-midnight)]">
                Cross-Vector Risk Correlation
              </span>
            </div>
            <span className="text-[10px] font-mono font-bold text-violet-600 px-2 py-0.5 rounded-full bg-violet-50 border border-violet-200">
              Risk Calibration: {adjustment >= 0 ? `+${adjustment}` : adjustment}
            </span>
          </div>
          <p className="text-xs text-[var(--color-text-secondary)] leading-relaxed mb-2">
            {verdict.rationale}
          </p>
          {verdict.cited_evidence && verdict.cited_evidence.length > 0 && (
            <div className="text-[10px] font-mono text-slate-500 flex items-center gap-2">
              <span>Supporting Signals:</span>
              <span className="text-violet-700 font-semibold">
                {verdict.cited_evidence.join(", ")}
              </span>
            </div>
          )}
        </div>

        {/* Step 4: Policy Engine & Actuation */}
        <div className="p-4 rounded-2xl bg-[var(--color-surface-subtle)] border border-[var(--color-border)]">
          <div className="flex items-center justify-between mb-1.5">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-600" />
              <span className="text-xs font-bold text-[var(--color-brand-midnight)]">
                Safety Policy & Enforcement Engine
              </span>
            </div>
            <span className="text-[10px] font-mono font-bold text-slate-700">Bank Policy</span>
          </div>
          <div className="text-xs text-[var(--color-text-secondary)] space-y-1">
            <div>
              Final Decision: <strong className="text-[var(--color-brand-midnight)]">{verdict.decision}</strong> (Risk Tier: {verdict.risk_level})
            </div>
            {rules.length > 0 && (
              <div className="text-rose-700 font-medium">
                Mandatory Safety Policy Triggered: {rules.join(", ")} (Score Floor: {breakdown?.floor ?? 0})
              </div>
            )}
            {actuator && (
              <div className="text-[11px] font-mono text-slate-600 pt-1">
                Protection Status: Account Frozen = {String(actuator.account_locked)}, Transfer Blocked = {String(actuator.tx_blocked)}, Early Containment = {String(actuator.early_containment)}
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
