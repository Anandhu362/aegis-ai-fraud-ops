import React, { useState } from "react";
import {
  Clock,
  CheckCircle2,
  AlertTriangle,
} from "lucide-react";
import type { Verdict } from "../types/generated/verdict.v1";
import { ThreatGauge } from "./ThreatGauge";
import { AgentChatLog } from "./AgentChatLog";
import { AnalystActions } from "./AnalystActions";

interface CaseQueueViewProps {
  cases: Verdict[];
  onDecisionRecorded: (updatedVerdict: Verdict) => void;
  userRole: string;
}

export function CaseQueueView({
  cases,
  onDecisionRecorded,
}: CaseQueueViewProps): React.JSX.Element {
  // Escalations are cases that require analyst intervention (Score 30-84 or decision REVIEW / CHALLENGE_3DS)
  const escalationCases = cases.filter(
    (c) =>
      c.decision === "REVIEW" ||
      c.decision === "CHALLENGE_3DS" ||
      (c.threat_score >= 30 && c.threat_score <= 84)
  );

  const [selectedTxId, setSelectedTxId] = useState<string | null>(
    escalationCases[0]?.tx_id ?? null
  );

  const activeCase =
    escalationCases.find((c) => c.tx_id === selectedTxId) ??
    escalationCases[0] ??
    null;

  return (
    <div className="flex flex-col gap-6">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-6 rounded-[28px] bg-white border border-[var(--color-border)] shadow-[var(--shadow-card)]">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-50 text-amber-800 border border-amber-200 text-xs font-semibold mb-2">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
            <span>Escalation Queue • Priority Triage</span>
          </div>
          <h2 className="text-xl sm:text-2xl font-black text-[var(--color-brand-midnight)] tracking-tight">
            Manual Review & Human-in-the-Loop Workbench
          </h2>
          <p className="text-xs text-[var(--color-text-secondary)] mt-1 max-w-2xl leading-relaxed">
            Transactions scoring in the elevated risk band (30–84) or subject to step-up authentication. Authorized fraud analysts can inspect multi-agent reasoning, record audited overrides, and release false positives.
          </p>
        </div>

        <div className="flex items-center gap-3 bg-[var(--color-surface-subtle)] border border-[var(--color-border)] rounded-2xl px-5 py-3">
          <div className="w-10 h-10 rounded-xl bg-amber-50 text-amber-700 flex items-center justify-center font-bold text-lg font-mono">
            {escalationCases.length}
          </div>
          <div className="flex flex-col">
            <span className="text-xs font-bold text-[var(--color-brand-midnight)]">
              Pending Reviews
            </span>
            <span className="text-[10px] text-[var(--color-text-muted)]">
              Target SLA: &lt; 2 minutes
            </span>
          </div>
        </div>
      </div>

      {escalationCases.length === 0 ? (
        <div className="py-24 px-6 text-center flex flex-col items-center justify-center gap-4 bg-white rounded-[28px] border border-[var(--color-border)] shadow-[var(--shadow-card)]">
          <div className="w-16 h-16 rounded-3xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
            <CheckCircle2 className="w-8 h-8" />
          </div>
          <div className="max-w-md">
            <h3 className="text-base font-bold text-[var(--color-brand-midnight)]">
              Escalation Queue Clean
            </h3>
            <p className="text-xs text-[var(--color-text-secondary)] mt-1.5 leading-relaxed">
              No transactions currently require manual review. All recent transactions were either auto-approved via Fast-Path (&lt; 700ms) or contained autonomously by risk policies.
            </p>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Column: Escalated Cases List */}
          <div className="lg:col-span-5 flex flex-col gap-3 max-h-[750px] overflow-y-auto pr-1">
            {escalationCases.map((c) => {
              const isSelected = (activeCase?.tx_id === c.tx_id);
              return (
                <div
                  key={c.tx_id}
                  onClick={() => setSelectedTxId(c.tx_id)}
                  className={`p-4 rounded-2xl border transition-all cursor-pointer ${
                    isSelected
                      ? "bg-white border-violet-500 shadow-md ring-2 ring-violet-500/10"
                      : "bg-white hover:bg-[var(--color-surface-subtle)] border-[var(--color-border)] shadow-xs"
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-bold font-mono text-[var(--color-brand-midnight)]">
                      {c.tx_id}
                    </span>
                    <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-amber-50 text-amber-800 border border-amber-200">
                      {c.decision}
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-xs font-medium text-slate-700 mb-1">
                    <span className="font-mono text-slate-500">{c.user_id}</span>
                    <span className="text-rose-700 font-bold font-mono">
                      Threat Score: {c.threat_score}/100
                    </span>
                  </div>

                  <p className="text-[11px] text-[var(--color-text-secondary)] line-clamp-2 leading-relaxed">
                    {c.rationale}
                  </p>
                </div>
              );
            })}
          </div>

          {/* Right Column: Case Details & Analyst Workbench */}
          <div className="lg:col-span-7 flex flex-col gap-6">
            {activeCase && (
              <div className="bg-white rounded-[28px] border border-[var(--color-border)] shadow-[var(--shadow-floating)] p-6 lg:p-8 flex flex-col gap-6">
                <div className="flex items-center justify-between border-b border-[var(--color-border)] pb-4">
                  <div>
                    <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400">
                      Case Inspection Workbench
                    </span>
                    <h3 className="text-lg font-bold text-[var(--color-brand-midnight)] font-mono">
                      {activeCase.tx_id} • {activeCase.user_id}
                    </h3>
                  </div>
                  <span className="text-xs font-bold font-mono px-3 py-1 rounded-full bg-amber-50 text-amber-800 border border-amber-200">
                    STATUS: PENDING REVIEW
                  </span>
                </div>

                {/* Threat Gauge */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <ThreatGauge
                    score={activeCase.threat_score}
                    riskLevel={activeCase.risk_level}
                    hardFloor={activeCase.score_breakdown?.floor ?? 0}
                  />

                  <div className="p-5 rounded-2xl bg-[var(--color-surface-subtle)] border border-[var(--color-border)] flex flex-col justify-between">
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <Clock className="w-4 h-4 text-amber-600" />
                        <span className="text-xs font-bold text-[var(--color-brand-midnight)]">
                          SLA Priority Escalation
                        </span>
                      </div>
                      <p className="text-[11px] text-[var(--color-text-secondary)] leading-relaxed">
                        Enforced by banking risk thresholds. This case presents elevated behavioral anomalies or 3DS verification latency.
                      </p>
                    </div>
                    <div className="text-[10px] font-mono text-slate-500 pt-2 border-t border-[var(--color-border)]">
                      Typology: <strong className="text-slate-800">{activeCase.typology}</strong>
                    </div>
                  </div>
                </div>

                {/* Multi-Agent Reasoning */}
                <AgentChatLog verdict={activeCase} />

                {/* Analyst Action Controls */}
                <AnalystActions
                  verdict={activeCase}
                  onDecisionRecorded={onDecisionRecorded}
                />
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
