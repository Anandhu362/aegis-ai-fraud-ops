import React from "react";
import { CreditCard, Landmark, Globe } from "lucide-react";

export function SimulationBar(): React.JSX.Element {
  return (
    <div className="pt-6">
      {/* Ribbon Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3">
        <span className="text-xs font-bold uppercase tracking-wider text-[var(--color-text-muted)] font-mono flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          Preloaded Core Banking Channels &amp; Surveillance Rails
        </span>
        <div className="flex items-center gap-2 text-[11px] font-mono text-slate-500">
          <span className="w-1.5 h-1.5 rounded-full bg-cyan-500" />
          <span>Real-Time Ingestion Active • 1,240 tx/s • Zero Packet Loss</span>
        </div>
      </div>

      {/* 3 Preloaded Operational Status Cards (Non-Clickable Genuine Banking Telemetry) */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* Channel 1: Retail POS & Card Clearing */}
        <div className="p-4 rounded-2xl bg-[var(--color-surface-subtle)] border border-[var(--color-border)] flex items-start justify-between gap-3 shadow-2xs">
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center border border-emerald-100 shrink-0">
              <CreditCard className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-[var(--color-brand-midnight)]">
                  Retail POS &amp; Card Clearing
                </span>
              </div>
              <div className="text-[11px] text-[var(--color-text-secondary)] mt-0.5 leading-relaxed">
                Preloaded Visa / Mastercard ISO 8583 feed. Routine spend &lt; $100 approved in &lt; 700ms.
              </div>
            </div>
          </div>
          <span className="text-[10px] font-mono font-bold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200 shrink-0">
            FAST-PATH
          </span>
        </div>

        {/* Channel 2: Fedwire & RTP Velocity Surveillance */}
        <div className="p-4 rounded-2xl bg-[var(--color-surface-subtle)] border border-[var(--color-border)] flex items-start justify-between gap-3 shadow-2xs">
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center border border-amber-100 shrink-0">
              <Landmark className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-[var(--color-brand-midnight)]">
                  Fedwire &amp; RTP Surveillance
                </span>
              </div>
              <div className="text-[11px] text-[var(--color-text-secondary)] mt-0.5 leading-relaxed">
                Preloaded BSA/AML velocity filter. $9,000–$9,999 structuring burst surveillance active.
              </div>
            </div>
          </div>
          <span className="text-[10px] font-mono font-bold text-amber-700 bg-amber-50 px-2.5 py-1 rounded-full border border-amber-200 shrink-0">
            RULE H2
          </span>
        </div>

        {/* Channel 3: Cross-Border & Geo-Firewall */}
        <div className="p-4 rounded-2xl bg-[var(--color-surface-subtle)] border border-[var(--color-border)] flex items-start justify-between gap-3 shadow-2xs">
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 rounded-xl bg-rose-50 text-rose-600 flex items-center justify-center border border-rose-100 shrink-0">
              <Globe className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-[var(--color-brand-midnight)]">
                  Cross-Border Geo-Firewall
                </span>
              </div>
              <div className="text-[11px] text-[var(--color-text-secondary)] mt-0.5 leading-relaxed">
                Preloaded Tor/VPN IP intel &amp; impossible travel (&gt;800 km/h) account containment.
              </div>
            </div>
          </div>
          <span className="text-[10px] font-mono font-bold text-rose-700 bg-rose-50 px-2.5 py-1 rounded-full border border-rose-200 shrink-0">
            RULE H1
          </span>
        </div>
      </div>
    </div>
  );
}

export default SimulationBar;
