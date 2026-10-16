import React from "react";
import {
  Cpu,
  Database,
  ShieldCheck,
  Gauge,
  AlertCircle,
  Activity,
} from "lucide-react";
import type { MetricsSummary } from "../services/api";

interface ApiQuotaViewProps {
  metrics: MetricsSummary;
}

export function ApiQuotaView({ metrics }: ApiQuotaViewProps): React.JSX.Element {
  const isDegraded = metrics.degraded_mode ?? false;

  return (
    <div className="flex flex-col gap-6">
      {/* Top Banner */}
      <div className="p-6 rounded-[28px] bg-white border border-[var(--color-border)] shadow-[var(--shadow-card)] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-violet-50 text-violet-800 border border-violet-200 text-xs font-semibold mb-2">
            <Cpu className="w-3.5 h-3.5 text-violet-600" />
            <span>Infrastructure Health &amp; Capacity Limits</span>
          </div>
          <h2 className="text-xl sm:text-2xl font-black text-[var(--color-brand-midnight)] tracking-tight">
            API Rate Limiting, Abuse Prevention &amp; Quotas
          </h2>
          <p className="text-xs text-[var(--color-text-secondary)] mt-1 max-w-2xl leading-relaxed">
            Autonomous protection against quota exhaustion, API rate limits, and DDoS traffic. Enforces dual token-bucket rate limiting and automatic graceful degradation to deterministic policies.
          </p>
        </div>

        <div className="flex items-center gap-2 bg-emerald-50 text-emerald-800 border border-emerald-200 px-4 py-2 rounded-2xl text-xs font-mono font-bold">
          <ShieldCheck className="w-4 h-4 text-emerald-600" />
          <span>All Microservices Healthy</span>
        </div>
      </div>

      {/* Degraded mode status */}
      <div
        className={`p-4 rounded-2xl border flex items-center justify-between gap-4 ${
          isDegraded
            ? "bg-amber-50 border-amber-200 text-amber-900"
            : "bg-emerald-50/70 border-emerald-200 text-emerald-900"
        }`}
      >
        <div className="flex items-center gap-3">
          {isDegraded ? (
            <AlertCircle className="w-5 h-5 text-amber-600 shrink-0" />
          ) : (
            <ShieldCheck className="w-5 h-5 text-emerald-600 shrink-0" />
          )}
          <div>
            <div className="text-xs font-bold">
              {isDegraded
                ? "[SURGE PROTECTION ACTIVE] Ingestion Concurrency Throttled"
                : "Standard Surveillance Mode Active — Dual-Tier Banking Defense"}
            </div>
            <div className="text-[11px] opacity-90 mt-0.5">
              {isDegraded
                ? "Surge transactions automatically routed to deterministic policy engine to maintain zero transaction delay."
                : "All specialist evaluation vectors and Deterministic Fast-Path gates are operating within approved banking thresholds."}
            </div>
          </div>
        </div>
        <span className="text-xs font-mono font-bold px-3 py-1 rounded-full bg-white border border-current shrink-0">
          {isDegraded ? "DEGRADED" : "OPTIMAL"}
        </span>
      </div>

      {/* Quotas Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Card 1: Ingestion Rate Limiter */}
        <div className="p-6 rounded-[28px] bg-white border border-[var(--color-border)] shadow-[var(--shadow-card)] flex flex-col justify-between gap-4">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-[var(--color-brand-midnight)] flex items-center gap-2">
                <Gauge className="w-4 h-4 text-violet-600" />
                Ingestion Token Bucket
              </span>
              <span className="text-[10px] font-mono text-emerald-700 font-bold bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                ACTIVE
              </span>
            </div>
            <p className="text-xs text-[var(--color-text-secondary)] leading-relaxed">
              Global intake protection shielding the API Gateway against flood attacks and runaway simulator scripts.
            </p>
          </div>

          <div className="p-4 rounded-2xl bg-[var(--color-surface-subtle)] border border-[var(--color-border)] space-y-2 text-xs font-mono">
            <div className="flex items-center justify-between">
              <span className="text-slate-500">Global Limit:</span>
              <strong className="text-[var(--color-brand-midnight)]">60 requests / min</strong>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-500">Refill Rate:</span>
              <strong className="text-emerald-700">1 token / second</strong>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-500">Drop Policy:</span>
              <strong className="text-rose-700">HTTP 429 Too Many Requests</strong>
            </div>
          </div>
        </div>

        {/* Card 2: AI Concurrency Cap */}
        <div className="p-6 rounded-[28px] bg-white border border-[var(--color-border)] shadow-[var(--shadow-card)] flex flex-col justify-between gap-4">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-[var(--color-brand-midnight)] flex items-center gap-2">
                <Activity className="w-4 h-4 text-cyan-600" />
                High-Risk Surveillance Capacity Cap
              </span>
              <span className="text-[10px] font-mono text-cyan-700 font-bold bg-cyan-50 px-2 py-0.5 rounded-full border border-cyan-200">
                15 RPM CAP
              </span>
            </div>
            <p className="text-xs text-[var(--color-text-secondary)] leading-relaxed">
              Protects core banking pipelines against concurrency spikes and DDoS bursts during peak transaction clearing.
            </p>
          </div>

          <div className="p-4 rounded-2xl bg-[var(--color-surface-subtle)] border border-[var(--color-border)] space-y-2 text-xs font-mono">
            <div className="flex items-center justify-between">
              <span className="text-slate-500">Max Deep Evaluations:</span>
              <strong className="text-[var(--color-brand-midnight)]">15 evaluations / min</strong>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-500">Surge Routing:</span>
              <strong className="text-violet-700">Tier-1 Deterministic Guardrails</strong>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-500">Zero Crash SLA:</span>
              <strong className="text-emerald-700">Active Fallback</strong>
            </div>
          </div>
        </div>

        {/* Card 3: Storage & Telemetry Endpoints */}
        <div className="p-6 rounded-[28px] bg-white border border-[var(--color-border)] shadow-[var(--shadow-card)] flex flex-col justify-between gap-4">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-[var(--color-brand-midnight)] flex items-center gap-2">
                <Database className="w-4 h-4 text-emerald-600" />
                Storage & Audit Backends
              </span>
              <span className="text-[10px] font-mono text-emerald-700 font-bold bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                CONNECTED
              </span>
            </div>
            <p className="text-xs text-[var(--color-text-secondary)] leading-relaxed">
              Google Cloud Firestore Native case store and BigQuery cold telemetry sink status.
            </p>
          </div>

          <div className="p-4 rounded-2xl bg-[var(--color-surface-subtle)] border border-[var(--color-border)] space-y-2 text-xs font-mono">
            <div className="flex items-center justify-between">
              <span className="text-slate-500">Hot-Cache Shield:</span>
              <strong className="text-emerald-700">$0 Read Spikes (RAM)</strong>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-500">Firestore Native:</span>
              <strong className="text-[var(--color-brand-midnight)]">investigations</strong>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-500">BigQuery Cold Sink:</span>
              <strong className="text-[var(--color-brand-midnight)]">investigation_results</strong>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
