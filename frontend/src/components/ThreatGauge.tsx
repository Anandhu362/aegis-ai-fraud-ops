import React from "react";

interface ThreatGaugeProps {
  score: number;
  riskLevel: "LOW" | "ELEVATED" | "HIGH" | "CRITICAL";
  hardFloor?: number;
}

export function ThreatGauge({ score, riskLevel, hardFloor = 0 }: ThreatGaugeProps): React.JSX.Element {
  // Clamped angle calculation for 180-degree semi-circle gauge (from -90deg to +90deg)
  const clampedScore = Math.max(0, Math.min(100, score));
  const strokeDashoffset = 251.2 - (251.2 * clampedScore) / 100;

  const colorConfig = {
    LOW: {
      stroke: "#10B981",
      text: "text-emerald-700",
      bg: "bg-emerald-50",
      label: "LOW RISK",
    },
    ELEVATED: {
      stroke: "#F59E0B",
      text: "text-amber-800",
      bg: "bg-amber-50",
      label: "ELEVATED",
    },
    HIGH: {
      stroke: "#EA580C",
      text: "text-orange-800",
      bg: "bg-orange-50",
      label: "HIGH THREAT",
    },
    CRITICAL: {
      stroke: "#E11D48",
      text: "text-rose-800",
      bg: "bg-rose-50",
      label: "CRITICAL FRAUD",
    },
  }[riskLevel];

  return (
    <div className="flex flex-col items-center justify-center p-5 rounded-2xl bg-[var(--color-surface-subtle)] border border-[var(--color-border)] relative">
      <div className="w-full flex items-center justify-between mb-2">
        <span className="text-[11px] font-bold uppercase tracking-wider text-[var(--color-brand-midnight)]">
          Risk Assessment Gauge
        </span>
        {hardFloor > 0 && (
          <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded-full bg-rose-100 text-rose-700 border border-rose-200">
            Safety Floor {hardFloor}
          </span>
        )}
      </div>


      <div className="relative w-44 h-24 flex items-end justify-center">
        <svg viewBox="0 0 100 50" className="w-full h-full">
          {/* Background track */}
          <path
            d="M 10 50 A 40 40 0 0 1 90 50"
            fill="none"
            stroke="#E2E0EC"
            strokeWidth="10"
            strokeLinecap="round"
          />
          {/* Animated active stroke */}
          <path
            d="M 10 50 A 40 40 0 0 1 90 50"
            fill="none"
            stroke={colorConfig.stroke}
            strokeWidth="10"
            strokeLinecap="round"
            strokeDasharray="251.2"
            strokeDashoffset={strokeDashoffset}
            className="transition-all duration-700 ease-out"
          />
        </svg>

        {/* Score overlay in center */}
        <div className="absolute inset-0 flex flex-col items-center justify-end pb-1">
          <span className="text-3xl font-black font-mono tracking-tight text-[var(--color-brand-midnight)]">
            {clampedScore}
          </span>
          <span className="text-[10px] uppercase font-mono font-bold text-[var(--color-text-muted)]">
            Out of 100
          </span>
        </div>
      </div>

      <div className="mt-3">
        <span
          className={`text-[11px] font-mono font-bold px-3 py-1 rounded-full border ${colorConfig.bg} ${colorConfig.text}`}
        >
          {colorConfig.label}
        </span>
      </div>
    </div>
  );
}
