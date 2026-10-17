import React from "react";
import { CreditCard, Landmark, Globe, ShieldAlert, Play, Pause, Zap, ArrowRight, Loader2 } from "lucide-react";

export interface SimulationBarProps {
  onTriggerScenario: (scenario: "coffee" | "challenge_3ds" | "smurfing" | "tor_travel") => Promise<void>;
  loadingScenario: string | null;
  streaming: boolean;
  onToggleStreaming: () => void;
  onPopulateDemoData: () => Promise<void>;
  populating: boolean;
}

export function SimulationBar({
  onTriggerScenario,
  loadingScenario,
  streaming,
  onToggleStreaming,
  onPopulateDemoData,
  populating,
}: SimulationBarProps): React.JSX.Element {
  return (
    <div className="pt-6">
      {/* Ribbon Header with Streaming & Populate Controls */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3 mb-3">
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)] font-mono flex items-center gap-1.5">
            <span className={`w-2 h-2 rounded-full ${streaming ? "bg-emerald-500 animate-ping" : "bg-emerald-500 animate-pulse"}`} />
            Preloaded Core Banking Channels &amp; Surveillance Rails
          </span>
          {streaming && (
            <span className="text-[10px] font-mono font-bold text-emerald-800 bg-emerald-50 border border-emerald-300 px-2 py-0.5 rounded-full animate-pulse">
              LIVE STREAM ACTIVE (4.5s)
            </span>
          )}
        </div>

        {/* Interactive Judge Controls: Live Stream Toggle & Populate */}
        <div className="flex items-center gap-2 flex-wrap">
          <button
            type="button"
            onClick={onToggleStreaming}
            className={`px-3.5 py-1.5 rounded-xl font-mono text-xs font-semibold flex items-center gap-2 transition-all cursor-pointer shadow-xs ${
              streaming
                ? "bg-emerald-600 hover:bg-emerald-700 text-white shadow-emerald-600/30 ring-2 ring-emerald-500/40"
                : "bg-white hover:bg-slate-50 text-[var(--color-brand-midnight)] border border-[var(--color-border)] hover:border-slate-300"
            }`}
            title="Auto-generate live incoming banking transactions every 3.5 seconds"
          >
            {streaming ? (
              <>
                <Pause className="w-3.5 h-3.5 fill-current" />
                <span>Pause Live Stream</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-current text-emerald-600" />
                <span>Start Live Stream</span>
              </>
            )}
          </button>

          <button
            type="button"
            onClick={onPopulateDemoData}
            disabled={populating || streaming}
            className="px-3.5 py-1.5 rounded-xl font-mono text-xs font-semibold flex items-center gap-2 bg-white hover:bg-slate-50 text-[var(--color-brand-midnight)] border border-[var(--color-border)] hover:border-slate-300 transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed shadow-xs"
            title="Inject 4 verified benchmark cases: Clean POS, 3DS Step-Up, Structuring Smurfing, and Tor ATO Lockout"
          >
            {populating ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin text-amber-600" />
                <span>Populating Rails...</span>
              </>
            ) : (
              <>
                <Zap className="w-3.5 h-3.5 text-amber-500 fill-amber-500/20" />
                <span>Populate Demo Cases</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* 4 Interactive Banking Scenario Rails */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Channel 1: Retail POS & Card Clearing (Fast-Path) */}
        <div
          onClick={() => !loadingScenario && onTriggerScenario("coffee")}
          className={`group p-4 rounded-2xl bg-[var(--color-surface-subtle)] hover:bg-white border transition-all cursor-pointer shadow-2xs flex flex-col justify-between ${
            loadingScenario === "coffee"
              ? "border-emerald-500 ring-2 ring-emerald-500/20 bg-white"
              : "border-[var(--color-border)] hover:border-emerald-300"
          }`}
        >
          <div>
            <div className="flex items-start justify-between gap-2 mb-2">
              <div className="flex items-center gap-2.5">
                <div className="w-9 h-9 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center border border-emerald-100 shrink-0 group-hover:scale-105 transition-transform">
                  <CreditCard className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-xs font-bold text-[var(--color-brand-midnight)]">
                    Retail POS &amp; Card Clearing
                  </div>
                  <div className="text-[10px] font-mono text-emerald-700 font-semibold">
                    Visa / MC • Routine Spend &lt; $100
                  </div>
                </div>
              </div>
              <span className="text-[10px] font-mono font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200 shrink-0">
                FAST-PATH
              </span>
            </div>

            <p className="text-[11px] text-[var(--color-text-secondary)] leading-relaxed">
              Routine coffee shop transaction. Evaluates deterministic zero-LLM fast path in &lt; 700ms.
            </p>
          </div>

          <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
            <span className="text-[11px] font-mono text-slate-500">
              {loadingScenario === "coffee" ? "Analyzing Fast-Path..." : "Inject POS Tx ($4.50)"}
            </span>
            <div className="flex items-center gap-1 text-emerald-600 font-semibold text-[11px]">
              {loadingScenario === "coffee" ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <>
                  <span className="group-hover:underline">Trigger</span>
                  <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                </>
              )}
            </div>
          </div>
        </div>

        {/* Channel 2: eCommerce Card-Not-Present (Step-Up 3DS Challenge) */}
        <div
          onClick={() => !loadingScenario && onTriggerScenario("challenge_3ds")}
          className={`group p-4 rounded-2xl bg-[var(--color-surface-subtle)] hover:bg-white border transition-all cursor-pointer shadow-2xs flex flex-col justify-between ${
            loadingScenario === "challenge_3ds"
              ? "border-cyan-500 ring-2 ring-cyan-500/20 bg-white"
              : "border-[var(--color-border)] hover:border-cyan-300"
          }`}
        >
          <div>
            <div className="flex items-start justify-between gap-2 mb-2">
              <div className="flex items-center gap-2.5">
                <div className="w-9 h-9 rounded-xl bg-cyan-50 text-cyan-600 flex items-center justify-center border border-cyan-100 shrink-0 group-hover:scale-105 transition-transform">
                  <ShieldAlert className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-xs font-bold text-[var(--color-brand-midnight)]">
                    eCommerce &amp; Card-Not-Present
                  </div>
                  <div className="text-[10px] font-mono text-cyan-700 font-semibold">
                    Step-Up 3DS • $450 Electronics
                  </div>
                </div>
              </div>
              <span className="text-[10px] font-mono font-bold text-cyan-700 bg-cyan-50 px-2 py-0.5 rounded-full border border-cyan-200 shrink-0">
                RULE S1+S10
              </span>
            </div>

            <p className="text-[11px] text-[var(--color-text-secondary)] leading-relaxed">
              Novel merchant category on new device. Elevates risk score (31–70) and triggers SMS OTP challenge.
            </p>
          </div>

          <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
            <span className="text-[11px] font-mono text-slate-500">
              {loadingScenario === "challenge_3ds" ? "Initiating 3DS OTP..." : "Inject 3DS ($450)"}
            </span>
            <div className="flex items-center gap-1 text-cyan-600 font-semibold text-[11px]">
              {loadingScenario === "challenge_3ds" ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <>
                  <span className="group-hover:underline">Trigger</span>
                  <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                </>
              )}
            </div>
          </div>
        </div>

        {/* Channel 3: Fedwire & RTP Velocity Surveillance (Rule H2) */}
        <div
          onClick={() => !loadingScenario && onTriggerScenario("smurfing")}
          className={`group p-4 rounded-2xl bg-[var(--color-surface-subtle)] hover:bg-white border transition-all cursor-pointer shadow-2xs flex flex-col justify-between ${
            loadingScenario === "smurfing"
              ? "border-amber-500 ring-2 ring-amber-500/20 bg-white"
              : "border-[var(--color-border)] hover:border-amber-300"
          }`}
        >
          <div>
            <div className="flex items-start justify-between gap-2 mb-2">
              <div className="flex items-center gap-2.5">
                <div className="w-9 h-9 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center border border-amber-100 shrink-0 group-hover:scale-105 transition-transform">
                  <Landmark className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-xs font-bold text-[var(--color-brand-midnight)]">
                    Fedwire &amp; RTP Surveillance
                  </div>
                  <div className="text-[10px] font-mono text-amber-700 font-semibold">
                    BSA/AML Velocity • $9,800 Burst
                  </div>
                </div>
              </div>
              <span className="text-[10px] font-mono font-bold text-amber-700 bg-amber-50 px-2 py-0.5 rounded-full border border-amber-200 shrink-0">
                RULE H2
              </span>
            </div>

            <p className="text-[11px] text-[var(--color-text-secondary)] leading-relaxed">
              Near-threshold smurfing money transfer. Triggers structuring surveillance and specialist audit.
            </p>
          </div>

          <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
            <span className="text-[11px] font-mono text-slate-500">
              {loadingScenario === "smurfing" ? "Evaluating H2 Floor..." : "Inject Structuring ($9,800)"}
            </span>
            <div className="flex items-center gap-1 text-amber-600 font-semibold text-[11px]">
              {loadingScenario === "smurfing" ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <>
                  <span className="group-hover:underline">Trigger</span>
                  <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                </>
              )}
            </div>
          </div>
        </div>

        {/* Channel 3: Cross-Border & Geo-Firewall (Rule H1) */}
        <div
          onClick={() => !loadingScenario && onTriggerScenario("tor_travel")}
          className={`group p-4 rounded-2xl bg-[var(--color-surface-subtle)] hover:bg-white border transition-all cursor-pointer shadow-2xs flex flex-col justify-between ${
            loadingScenario === "tor_travel"
              ? "border-rose-500 ring-2 ring-rose-500/20 bg-white"
              : "border-[var(--color-border)] hover:border-rose-300"
          }`}
        >
          <div>
            <div className="flex items-start justify-between gap-2 mb-2">
              <div className="flex items-center gap-2.5">
                <div className="w-9 h-9 rounded-xl bg-rose-50 text-rose-600 flex items-center justify-center border border-rose-100 shrink-0 group-hover:scale-105 transition-transform">
                  <Globe className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-xs font-bold text-[var(--color-brand-midnight)]">
                    Cross-Border Geo-Firewall
                  </div>
                  <div className="text-[10px] font-mono text-rose-700 font-semibold">
                    Tor Exit Node • Impossible Travel
                  </div>
                </div>
              </div>
              <span className="text-[10px] font-mono font-bold text-rose-700 bg-rose-50 px-2 py-0.5 rounded-full border border-rose-200 shrink-0">
                RULE H1
              </span>
            </div>

            <p className="text-[11px] text-[var(--color-text-secondary)] leading-relaxed">
              Frankfurt Tor node following NY login. Correlates multi-agent signals to execute autonomous lockout.
            </p>
          </div>

          <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
            <span className="text-[11px] font-mono text-slate-500">
              {loadingScenario === "tor_travel" ? "Executing Containment..." : "Inject Tor ATO ($12,500)"}
            </span>
            <div className="flex items-center gap-1 text-rose-600 font-semibold text-[11px]">
              {loadingScenario === "tor_travel" ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <>
                  <span className="group-hover:underline">Trigger</span>
                  <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default SimulationBar;
