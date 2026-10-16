import React, { useState } from "react";
import { CheckCircle2, AlertOctagon, Unlock, Loader2, ArrowRight } from "lucide-react";
import { api } from "../services/api";
import type { Verdict } from "../types/generated/verdict.v1";

interface AnalystActionsProps {
  verdict: Verdict;
  onDecisionRecorded: (updatedVerdict: Verdict) => void;
}

export function AnalystActions({
  verdict,
  onDecisionRecorded,
}: AnalystActionsProps): React.JSX.Element {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [selectedAction, setSelectedAction] = useState<"APPROVE" | "CONFIRM_FRAUD" | "UNLOCK" | null>(
    null
  );
  const [reason, setReason] = useState("");

  const handleOpenAction = (action: "APPROVE" | "CONFIRM_FRAUD" | "UNLOCK") => {
    setSelectedAction(action);
    if (action === "APPROVE") {
      setReason("Autonomous verdict verified and audit trail confirmed by L2 analyst.");
    } else if (action === "CONFIRM_FRAUD") {
      setReason("Confirmed malicious attack cluster; escalated to fraud ring containment.");
    } else if (action === "UNLOCK") {
      setReason("Customer verified via out-of-band multi-factor authentication (false positive).");
    }
  };

  const handleConfirmAction = async () => {
    if (!selectedAction) return;
    try {
      setIsSubmitting(true);
      setStatusMessage(`Recording ${selectedAction}...`);
      const updated = await api.recordAnalystDecision(
        verdict.tx_id,
        selectedAction,
        reason || `Analyst manual action: ${selectedAction}`
      );
      setStatusMessage(`Successfully recorded ${selectedAction}`);
      setSelectedAction(null);
      setReason("");
      onDecisionRecorded(updated);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setStatusMessage(`Failed: ${msg}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="pt-4 border-t border-[var(--color-border)] flex flex-col gap-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-xs text-[var(--color-text-secondary)]">
          <span className="w-2 h-2 rounded-full bg-emerald-500" />
          <span>
            Analyst Role: <strong className="text-[var(--color-brand-midnight)]">L2 Senior Fraud Ops</strong>
          </span>
          {statusMessage && (
            <span className="text-[11px] font-mono text-[var(--color-brand-terracotta)] font-medium">
              ({statusMessage})
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          {/* Unlock Account button */}
          <button
            type="button"
            disabled={isSubmitting}
            onClick={() => handleOpenAction("UNLOCK")}
            className="px-3.5 py-1.5 rounded-full text-xs font-semibold bg-[var(--color-surface-subtle)] hover:bg-slate-200 text-[var(--color-brand-midnight)] border border-[var(--color-border)] transition-colors cursor-pointer flex items-center gap-1.5 disabled:opacity-50"
          >
            <Unlock className="w-3.5 h-3.5 text-slate-600" />
            <span>Unlock User</span>
          </button>

          {/* Confirm Fraud button */}
          <button
            type="button"
            disabled={isSubmitting}
            onClick={() => handleOpenAction("CONFIRM_FRAUD")}
            className="px-3.5 py-1.5 rounded-full text-xs font-semibold bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 transition-colors cursor-pointer flex items-center gap-1.5 disabled:opacity-50"
          >
            <AlertOctagon className="w-3.5 h-3.5 text-rose-600" />
            <span>Confirm Fraud</span>
          </button>

          {/* Approve Audit Trail button */}
          <button
            type="button"
            disabled={isSubmitting}
            onClick={() => handleOpenAction("APPROVE")}
            className="px-4 py-1.5 rounded-full text-xs font-semibold bg-[var(--color-brand-midnight)] hover:bg-[#201548] text-white transition-colors cursor-pointer flex items-center gap-1.5 disabled:opacity-50"
          >
            <span>Approve Audit</span>
            <CheckCircle2 className="w-3.5 h-3.5 text-violet-300" />
          </button>
        </div>
      </div>

      {/* Confirmation & Rationale Modal / Drawer */}
      {selectedAction && (
        <div className="p-4 rounded-2xl bg-[var(--color-surface-subtle)] border border-violet-200 shadow-sm flex flex-col gap-2.5 animate-fadeIn">
          <div className="flex items-center justify-between text-xs font-semibold text-[var(--color-brand-midnight)]">
            <span>Confirm Action: {selectedAction} for {verdict.tx_id}</span>
            <button
              type="button"
              onClick={() => setSelectedAction(null)}
              className="text-[11px] text-[var(--color-text-muted)] hover:text-[var(--color-brand-midnight)] cursor-pointer"
            >
              Cancel
            </button>
          </div>
          <input
            type="text"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Enter reason for audit record..."
            className="w-full text-xs px-3 py-2 rounded-xl bg-white border border-[var(--color-border)] focus:outline-none focus:ring-2 focus:ring-violet-400 font-sans"
          />
          <div className="flex justify-end gap-2">
            <button
              type="button"
              disabled={isSubmitting}
              onClick={handleConfirmAction}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-semibold bg-[var(--color-brand-midnight)] text-white hover:bg-[#22144d] cursor-pointer disabled:opacity-50"
            >
              {isSubmitting ? (
                <Loader2 className="w-3 h-3 animate-spin" />
              ) : (
                <ArrowRight className="w-3 h-3 text-violet-300" />
              )}
              <span>Submit Audit Decision</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
