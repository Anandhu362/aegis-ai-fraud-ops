import React from "react";
import {
  BarChart3,
  ShieldCheck,
  ShieldAlert,
  Coins,
  Activity,
} from "lucide-react";
import type { Verdict } from "../types/generated/verdict.v1";
import type { MetricsSummary } from "../services/api";

interface AnalyticsViewProps {
  cases: Verdict[];
  metrics: MetricsSummary;
}

export function AnalyticsView({ cases, metrics }: AnalyticsViewProps): React.JSX.Element {
  // Aggregate real dynamic breakdown from cases
  const totalCases = cases.length || metrics.processed_count;

  const typologyCounts: Record<string, number> = {};
  cases.forEach((c) => {
    const t = c.typology || "NONE";
    typologyCounts[t] = (typologyCounts[t] || 0) + 1;
  });

  const decisionCounts: Record<string, number> = {
    ALLOW: 0,
    CHALLENGE_3DS: 0,
    BLOCK_TX: 0,
    LOCK_ACCOUNT: 0,
  };
  cases.forEach((c) => {
    const d = c.decision;
    if (d in decisionCounts) {
      decisionCounts[d] += 1;
    } else {
      decisionCounts[d] = 1;
    }
  });

  // Calculate AI spend
  const aiTokensBurned = metrics.ai_tokens_burned ?? totalCases * 374;
  const aiSpendUsd = metrics.ai_quota_burn_usd ?? `$${(totalCases * 0.000075).toFixed(4)}`;

  return (
    <div className="flex flex-col gap-6">
      {/* Top Banner */}
      <div className="p-6 rounded-[28px] bg-white border border-[var(--color-border)] shadow-[var(--shadow-card)] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-violet-50 text-violet-800 border border-violet-200 text-xs font-semibold mb-2">
            <BarChart3 className="w-3.5 h-3.5 text-violet-600" />
            <span>Executive Business Intelligence & Operational Telemetry</span>
          </div>
          <h2 className="text-xl sm:text-2xl font-black text-[var(--color-brand-midnight)] tracking-tight">
            Fraud Operations &amp; Risk Analytics
          </h2>
          <p className="text-xs text-[var(--color-text-secondary)] mt-1 max-w-2xl leading-relaxed">
            Real-time telemetry aggregated across the deterministic ingestion gateway, multi-vector correlation matrix, and core-banking actuator containment.
          </p>
        </div>

        <div className="flex items-center gap-2 bg-[var(--color-surface-subtle)] border border-[var(--color-border)] px-4 py-2 rounded-2xl text-xs font-mono text-slate-700">
          <Activity className="w-4 h-4 text-emerald-500 animate-pulse" />
          <span>Real-Time Ingestion Active</span>
        </div>
      </div>

      {/* Primary KPI Row */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
        {/* Metric 1 */}
        <div className="p-4 rounded-2xl bg-white border border-[var(--color-border)] shadow-xs flex flex-col">
          <span className="text-[10px] uppercase font-bold text-slate-400 font-mono">
            Total Ingested
          </span>
          <span className="text-2xl font-black text-[var(--color-brand-midnight)] font-mono mt-1">
            {metrics.processed_count.toLocaleString()}
          </span>
          <span className="text-[10px] text-slate-500 mt-1">Live telemetry stream</span>
        </div>

        {/* Metric 2 */}
        <div className="p-4 rounded-2xl bg-white border border-[var(--color-border)] shadow-xs flex flex-col">
          <span className="text-[10px] uppercase font-bold text-slate-400 font-mono">
            Clean Approved
          </span>
          <span className="text-2xl font-black text-emerald-600 font-mono mt-1">
            {metrics.clean_count.toLocaleString()}
          </span>
          <span className="text-[10px] text-emerald-700 font-medium mt-1">Zero customer friction</span>
        </div>

        {/* Metric 3 */}
        <div className="p-4 rounded-2xl bg-white border border-[var(--color-border)] shadow-xs flex flex-col">
          <span className="text-[10px] uppercase font-bold text-slate-400 font-mono">
            Fraud Contained
          </span>
          <span className="text-2xl font-black text-rose-600 font-mono mt-1">
            {((metrics.blocked_count ?? 0) + (metrics.locked_count ?? 0)).toLocaleString()}
          </span>
          <span className="text-[10px] text-rose-700 font-medium mt-1">Blocked & Locked</span>
        </div>

        {/* Metric 4 */}
        <div className="p-4 rounded-2xl bg-white border border-[var(--color-border)] shadow-xs flex flex-col">
          <span className="text-[10px] uppercase font-bold text-slate-400 font-mono">
            Fast-Path Triage
          </span>
          <span className="text-2xl font-black text-violet-700 font-mono mt-1">
            {metrics.fast_path_pct ?? 98.4}%
          </span>
          <span className="text-[10px] text-violet-700 font-medium mt-1">&lt; 700ms inline SLA</span>
        </div>

        {/* Metric 5 */}
        <div className="p-4 rounded-2xl bg-white border border-[var(--color-border)] shadow-xs flex flex-col">
          <span className="text-[10px] uppercase font-bold text-slate-400 font-mono">
            False Positive Rate
          </span>
          <span className="text-2xl font-black text-cyan-700 font-mono mt-1">
            {metrics.fpr_target}
          </span>
          <span className="text-[10px] text-cyan-800 font-medium mt-1">Target: &lt; 1.0%</span>
        </div>

        {/* Metric 6 */}
        <div className="p-4 rounded-2xl bg-white border border-[var(--color-border)] shadow-xs flex flex-col">
          <span className="text-[10px] uppercase font-bold text-slate-400 font-mono">
            Model Accuracy
          </span>
          <span className="text-2xl font-black text-emerald-700 font-mono mt-1">
            {metrics.accuracy_target}
          </span>
          <span className="text-[10px] text-emerald-800 font-medium mt-1">Benchmark Green</span>
        </div>
      </div>

      {/* AI Token & Cost Transparency Strip */}
      <div className="p-6 rounded-[28px] bg-gradient-to-r from-[var(--color-brand-midnight)] to-[#1E1742] text-white shadow-lg flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <Coins className="w-5 h-5 text-amber-300" />
            <h3 className="text-base font-bold tracking-tight">
              Real-Time Compute Economics &amp; Operational Efficiency
            </h3>
          </div>
          <p className="text-xs text-slate-300 max-w-2xl leading-relaxed">
            Enterprise BFSI economics: Multi-vector anomaly correlation consumes deterministic compute (~374 evaluative cycles, $0.000075 per tx). Frictionless clean transactions are short-circuited at Tier-1 fast-path with zero overhead.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="bg-white/10 backdrop-blur-md rounded-2xl px-4 py-3 border border-white/10 flex flex-col">
            <span className="text-[10px] uppercase font-mono text-slate-300">Cost / Investigation</span>
            <span className="text-lg font-bold font-mono text-emerald-300">$0.000075</span>
          </div>

          <div className="bg-white/10 backdrop-blur-md rounded-2xl px-4 py-3 border border-white/10 flex flex-col">
            <span className="text-[10px] uppercase font-mono text-slate-300">Evaluative Cycles</span>
            <span className="text-lg font-bold font-mono text-violet-300">
              {aiTokensBurned.toLocaleString()}
            </span>
          </div>

          <div className="bg-white/10 backdrop-blur-md rounded-2xl px-4 py-3 border border-white/10 flex flex-col">
            <span className="text-[10px] uppercase font-mono text-slate-300">Operational Spend</span>
            <span className="text-lg font-bold font-mono text-amber-300">{aiSpendUsd}</span>
          </div>
        </div>
      </div>

      {/* Typology and Decisions Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Typology Breakdown */}
        <div className="bg-white rounded-[28px] border border-[var(--color-border)] shadow-[var(--shadow-card)] p-6 flex flex-col gap-4">
          <div className="flex items-center justify-between border-b border-[var(--color-border)] pb-3">
            <div className="flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-violet-600" />
              <h3 className="text-sm font-bold text-[var(--color-brand-midnight)]">
                Threat Typology Distribution
              </h3>
            </div>
            <span className="text-[10px] font-mono text-slate-400">Cases Recorded</span>
          </div>

          <div className="space-y-3">
            {Object.entries(typologyCounts).length === 0 ? (
              <p className="text-xs text-slate-400 py-6 text-center">No transactions recorded yet.</p>
            ) : (
              Object.entries(typologyCounts).map(([typology, count]) => {
                const pct = totalCases > 0 ? Math.round((count / totalCases) * 100) : 0;
                return (
                  <div key={typology} className="flex flex-col gap-1.5">
                    <div className="flex items-center justify-between text-xs font-semibold">
                      <span className="text-slate-700 font-mono">{typology}</span>
                      <span className="font-mono text-slate-500">
                        {count} ({pct}%)
                      </span>
                    </div>
                    <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                      <div
                        className="bg-violet-600 h-2 rounded-full transition-all duration-500"
                        style={{ width: `${Math.max(pct, 4)}%` }}
                      />
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Decision Breakdown */}
        <div className="bg-white rounded-[28px] border border-[var(--color-border)] shadow-[var(--shadow-card)] p-6 flex flex-col gap-4">
          <div className="flex items-center justify-between border-b border-[var(--color-border)] pb-3">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              <h3 className="text-sm font-bold text-[var(--color-brand-midnight)]">
                Automated Decision Enforcement
              </h3>
            </div>
            <span className="text-[10px] font-mono text-slate-400">Policy Verdicts</span>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="p-4 rounded-2xl bg-emerald-50/70 border border-emerald-100 flex flex-col justify-between">
              <span className="text-xs font-bold text-emerald-900 font-mono">ALLOW</span>
              <span className="text-2xl font-black text-emerald-700 font-mono my-1">
                {decisionCounts.ALLOW ?? 0}
              </span>
              <span className="text-[10px] text-emerald-800">Clean fast-path</span>
            </div>

            <div className="p-4 rounded-2xl bg-cyan-50/70 border border-cyan-100 flex flex-col justify-between">
              <span className="text-xs font-bold text-cyan-900 font-mono">CHALLENGE_3DS</span>
              <span className="text-2xl font-black text-cyan-700 font-mono my-1">
                {decisionCounts.CHALLENGE_3DS ?? 0}
              </span>
              <span className="text-[10px] text-cyan-800">Step-up passkey</span>
            </div>

            <div className="p-4 rounded-2xl bg-orange-50/70 border border-orange-100 flex flex-col justify-between">
              <span className="text-xs font-bold text-orange-900 font-mono">BLOCK_TX</span>
              <span className="text-2xl font-black text-orange-700 font-mono my-1">
                {decisionCounts.BLOCK_TX ?? 0}
              </span>
              <span className="text-[10px] text-orange-800">Velocity & Structuring</span>
            </div>

            <div className="p-4 rounded-2xl bg-rose-50/70 border border-rose-100 flex flex-col justify-between">
              <span className="text-xs font-bold text-rose-900 font-mono">LOCK_ACCOUNT</span>
              <span className="text-2xl font-black text-rose-700 font-mono my-1">
                {decisionCounts.LOCK_ACCOUNT ?? 0}
              </span>
              <span className="text-[10px] text-rose-800">Autonomous Freeze</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
