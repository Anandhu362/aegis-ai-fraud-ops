import React from "react";
import { Shield, Activity, Coffee, DollarSign, Globe, Lock, Cpu } from "lucide-react";
import { useUiStore } from "./store/uiStore";

export function App(): React.JSX.Element {
  const { selectedTxId } = useUiStore();

  return (
    <div className="min-h-screen bg-[var(--color-bg)] text-[var(--color-text)] flex flex-col font-sans selection:bg-[var(--color-brand)] selection:text-white">
      {/* Top Header */}
      <header className="border-b border-[var(--color-border)] bg-[var(--color-surface)] backdrop-blur-xl px-6 py-3.5 flex items-center justify-between sticky top-0 z-50">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-[var(--color-brand)] to-[var(--color-brand-2)] flex items-center justify-center shadow-lg shadow-[var(--color-brand)]/20">
            <Shield className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-semibold tracking-tight text-white">
                Aegis AI Fraud Ops
              </h1>
              <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded-full bg-[var(--color-brand)]/15 text-[var(--color-brand)] border border-[var(--color-brand)]/30 font-medium">
                SOC Baseline v1.0
              </span>
            </div>
            <p className="text-xs text-[var(--color-muted)]">
              Multi-Agent Real-time BFSI Fraud Defense
            </p>
          </div>
        </div>

        {/* System Health Indicators */}
        <div className="flex items-center gap-6 text-xs font-mono">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[var(--color-risk-low)] animate-pulse" />
            <span className="text-[var(--color-muted)]">ADK Engine:</span>
            <span className="text-emerald-400">READY</span>
          </div>
          <div className="flex items-center gap-2">
            <Cpu className="w-3.5 h-3.5 text-[var(--color-brand-2)]" />
            <span className="text-[var(--color-muted)]">Gemini:</span>
            <span className="text-cyan-300">FLASH-LITE / FLASH</span>
          </div>
          <div className="flex items-center gap-2">
            <Activity className="w-3.5 h-3.5 text-[var(--color-brand)]" />
            <span className="text-[var(--color-muted)]">Target Latency:</span>
            <span className="text-white">&lt; 2.8s</span>
          </div>
        </div>
      </header>

      {/* Simulation Bar */}
      <section className="bg-[var(--color-surface)]/60 border-b border-[var(--color-border)] px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-[var(--color-muted)] uppercase tracking-wider mr-2">
            Test Scenarios:
          </span>
          <button
            type="button"
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 hover:bg-emerald-500/20 transition-all cursor-pointer"
          >
            <Coffee className="w-3.5 h-3.5" />
            <span>Clean Coffee ($4.50)</span>
            <span className="text-[10px] font-mono text-emerald-500/70 ml-1">&lt;1s Fast Path</span>
          </button>
          <button
            type="button"
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20 hover:bg-amber-500/20 transition-all cursor-pointer"
          >
            <DollarSign className="w-3.5 h-3.5" />
            <span>Smurfing ($9,800)</span>
            <span className="text-[10px] font-mono text-amber-500/70 ml-1">Structuring Burst</span>
          </button>
          <button
            type="button"
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium bg-rose-500/10 text-rose-400 border border-rose-500/20 hover:bg-rose-500/20 transition-all cursor-pointer"
          >
            <Globe className="w-3.5 h-3.5" />
            <span>Tor Impossible Travel ($12,500)</span>
            <span className="text-[10px] font-mono text-rose-500/70 ml-1">Early Lockout</span>
          </button>
        </div>

        <div className="text-xs font-mono text-[var(--color-muted)] flex items-center gap-2">
          <Lock className="w-3.5 h-3.5 text-rose-400" />
          <span>Policy Engine: Deterministic Floors Active</span>
        </div>
      </section>

      {/* Main Layout: Feed (40%) & Investigation View (60%) */}
      <main className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-6 p-6 max-w-[1920px] w-full mx-auto">
        {/* Transaction Feed (5 cols) */}
        <section className="lg:col-span-5 flex flex-col rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] backdrop-blur-xl overflow-hidden shadow-[var(--shadow-glow)]">
          <div className="p-4 border-b border-[var(--color-border)] flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-[var(--color-brand)]" />
              <h2 className="text-sm font-semibold text-white">Live Transaction Ingestion Feed</h2>
            </div>
            <span className="text-xs font-mono text-[var(--color-muted)]">Rolling 50</span>
          </div>
          <div className="flex-1 p-6 flex flex-col items-center justify-center text-center text-[var(--color-muted)]">
            <div className="w-12 h-12 rounded-full bg-white/5 flex items-center justify-center mb-3">
              <Activity className="w-6 h-6 text-[var(--color-muted)] animate-pulse" />
            </div>
            <p className="text-sm font-medium text-white mb-1">Awaiting Inbound Transactions</p>
            <p className="text-xs max-w-xs">
              Click a test scenario above or POST transactions to <code className="text-cyan-300">/v1/transactions:analyze</code>
            </p>
          </div>
        </section>

        {/* Investigation View (7 cols) */}
        <section className="lg:col-span-7 flex flex-col rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] backdrop-blur-xl overflow-hidden shadow-[var(--shadow-glow)]">
          <div className="p-4 border-b border-[var(--color-border)] flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Shield className="w-4 h-4 text-[var(--color-brand-2)]" />
              <h2 className="text-sm font-semibold text-white">Active Case Investigation</h2>
            </div>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-white/5 text-[var(--color-muted)]">
              {selectedTxId ?? "NO CASE SELECTED"}
            </span>
          </div>

          <div className="flex-1 p-6 flex flex-col items-center justify-center text-center text-[var(--color-muted)]">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-[var(--color-brand)]/20 to-[var(--color-brand-2)]/20 border border-white/10 flex items-center justify-center mb-4">
              <Shield className="w-8 h-8 text-[var(--color-brand)]" />
            </div>
            <h3 className="text-base font-semibold text-white mb-2">SOC Investigation Terminal</h3>
            <p className="text-xs max-w-md leading-relaxed">
              When a suspicious transaction is detected, this panel streams real-time reasoning steps from the <strong className="text-white">Behavioral Analyst</strong> and <strong className="text-white">Threat Intel</strong> agents, followed by the <strong className="text-white">Orchestrator</strong> synthesis and deterministic policy actions.
            </p>
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;
