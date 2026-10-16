import React from "react";
import { useUiStore } from "../store/uiStore";
import type { Verdict } from "../types/generated/verdict.v1";

interface TransactionFeedProps {
  cases: Verdict[];
  onSelectCase: (txId: string) => void;
}

export function TransactionFeed({ cases, onSelectCase }: TransactionFeedProps): React.JSX.Element {
  const { selectedTxId } = useUiStore();

  const getBadgeStyle = (decision: string) => {
    switch (decision) {
      case "ALLOW":
        return "bg-emerald-50 text-emerald-700 border-emerald-200";
      case "REVIEW":
        return "bg-amber-50 text-amber-700 border-amber-200";
      case "CHALLENGE_3DS":
        return "bg-cyan-50 text-cyan-800 border-cyan-300";
      case "CARD_SUSPENDED":
        return "bg-purple-50 text-purple-800 border-purple-300";
      case "BLOCK_TX":
        return "bg-orange-50 text-orange-800 border-orange-200";
      case "LOCK_ACCOUNT":
      case "DECLINE_LOCKED":
        return "bg-rose-50 text-rose-800 border-rose-200";
      default:
        return "bg-slate-50 text-slate-700 border-slate-200";
    }
  };

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between px-2">
        <span className="text-xs font-bold uppercase tracking-wider text-[var(--color-text-secondary)] flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-[var(--color-brand-violet)] animate-pulse" />
          Live Ingestion Feed
        </span>
        <span className="text-xs font-mono text-[var(--color-text-muted)]">
          {cases.length} Investigations
        </span>
      </div>

      <div className="bg-white rounded-[28px] border border-[var(--color-border)] shadow-[var(--shadow-floating)] p-4 flex flex-col gap-3 max-h-[680px] overflow-y-auto">
        {cases.length === 0 ? (
          <div className="py-16 px-4 text-center flex flex-col items-center justify-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-slate-100 flex items-center justify-center text-slate-400">
              <span className="w-2.5 h-2.5 rounded-full bg-violet-500 animate-ping" />
            </div>
            <div>
              <p className="text-xs font-semibold text-[var(--color-brand-midnight)]">
                Live Feed Standby
              </p>
              <p className="text-[11px] text-[var(--color-text-muted)] mt-1 max-w-[280px] mx-auto leading-relaxed">
                Listening on preloaded gateway channels. Click any surveillance rail above or &ldquo;Start Live Stream&rdquo; to simulate real-time banking transactions.
              </p>
            </div>
          </div>
        ) : (
          cases.map((verdict) => {
            const isSelected = verdict.tx_id === selectedTxId;
            const badgeClass = getBadgeStyle(verdict.decision);
            const latency = verdict.latency_ms?.total ?? 0;

            return (
              <div
                key={verdict.tx_id}
                onClick={() => onSelectCase(verdict.tx_id)}
                className={`p-4 rounded-2xl border transition-all cursor-pointer ${
                  isSelected
                    ? "bg-white border-[var(--color-brand-violet)] shadow-md ring-2 ring-violet-500/10"
                    : "bg-[var(--color-surface-subtle)] hover:bg-white border-[var(--color-border)]"
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-bold text-[var(--color-brand-midnight)] font-mono">
                      {verdict.tx_id}
                    </span>
                    <span className="text-xs text-[var(--color-text-muted)] font-mono">
                      {verdict.user_id}
                    </span>
                  </div>
                  <span
                    className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded-full border ${badgeClass}`}
                  >
                    {verdict.decision}
                  </span>
                </div>

                <div className="text-xs font-medium text-[var(--color-brand-midnight)] mb-1 flex items-center justify-between">
                  <span>Typology: <strong>{verdict.typology}</strong></span>
                  <span className="font-mono text-[var(--color-brand-terracotta)] font-bold">
                    Score: {verdict.threat_score}/100
                  </span>
                </div>

                <div className="text-[11px] text-[var(--color-text-secondary)] line-clamp-2 mb-2 leading-relaxed">
                  {verdict.rationale}
                </div>

                <div className="flex items-center justify-between text-[10px] font-mono text-[var(--color-text-muted)] pt-2 border-t border-[var(--color-border)]">
                  <span>Latency: {latency > 0 ? `${latency} ms` : "< 1.0s fast-path"}</span>
                  <span>{verdict.risk_level}</span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
