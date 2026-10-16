import React from "react";
import { Lock, ShieldAlert, KeyRound } from "lucide-react";
import type { Verdict } from "../types/generated/verdict.v1";

interface LockBannerProps {
  verdict: Verdict;
  onUnlockClick?: () => void;
}

export function LockBanner({ verdict, onUnlockClick }: LockBannerProps): React.JSX.Element | null {
  const isLocked =
    verdict.decision === "LOCK_ACCOUNT" ||
    verdict.decision === "DECLINE_LOCKED" ||
    verdict.decision === "CARD_SUSPENDED" ||
    verdict.actuator_action?.action === "lock_account";

  if (!isLocked) {
    return null;
  }

  const hardFloorRules = verdict.score_breakdown?.rules ?? [];
  const ruleDisplay = hardFloorRules.length > 0 ? hardFloorRules.join(", ") : "H1 (Tor ATO)";
  const actuatorStatus = typeof verdict.actuator_action?.status === "string" ? verdict.actuator_action.status : "EXECUTED";
  const idempotencyKey = typeof verdict.actuator_action?.idempotency_key === "string" ? verdict.actuator_action.idempotency_key : null;

  return (
    <div className="p-4 rounded-2xl bg-rose-50/80 border border-rose-200 shadow-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 text-rose-950 transition-all">
      <div className="flex items-start gap-3.5">
        <div className="p-2.5 rounded-xl bg-rose-100/90 text-rose-700 shrink-0 mt-0.5 sm:mt-0">
          <Lock className="w-5 h-5" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold uppercase tracking-wider text-rose-800">
              Safety Containment: Account Safeguarded
            </span>
            <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded-full bg-rose-200/80 text-rose-900 border border-rose-300">
              {actuatorStatus}
            </span>
          </div>
          <p className="text-xs text-rose-800/90 mt-1 leading-relaxed">
            Customer account <strong>{verdict.user_id}</strong> was automatically protected against unauthorized access (<strong>{ruleDisplay}</strong>). Outbound transfers isolated and instant customer verification alert dispatched.
          </p>
          {idempotencyKey && (
            <div className="mt-1 flex items-center gap-1.5 text-[10px] font-mono text-rose-700/80">
              <KeyRound className="w-3 h-3" />
              <span>Audit Ref: {idempotencyKey.slice(0, 24)}...</span>
            </div>
          )}

        </div>
      </div>

      {onUnlockClick && (
        <button
          type="button"
          onClick={onUnlockClick}
          className="shrink-0 flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-semibold bg-white hover:bg-rose-100 text-rose-700 border border-rose-300 shadow-2xs transition-colors cursor-pointer"
        >
          <ShieldAlert className="w-3.5 h-3.5 text-rose-600" />
          <span>Analyst Release</span>
        </button>
      )}
    </div>
  );
}
