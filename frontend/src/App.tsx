import React, { useState, useEffect } from "react";
import {
  Shield,
  Lock,
  Layers,
  Radio,
  RotateCcw,
  LogOut,
  Activity,
  CheckCircle2,
} from "lucide-react";
import { useUiStore } from "./store/uiStore";
import { SimulationBar } from "./components/SimulationBar";
import { TransactionFeed } from "./components/TransactionFeed";
import { ThreatGauge } from "./components/ThreatGauge";
import { AgentChatLog } from "./components/AgentChatLog";
import { LockBanner } from "./components/LockBanner";
import { AnalystActions } from "./components/AnalystActions";
import {
  NavigationSidebar,
  type NavTabId,
} from "./components/NavigationSidebar";
import { CaseQueueView } from "./components/CaseQueueView";
import { PolicyEngineView } from "./components/PolicyEngineView";
import { AnalyticsView } from "./components/AnalyticsView";
import { ApiQuotaView } from "./components/ApiQuotaView";
import { LoginModal } from "./components/LoginModal";
import { FintechDropdown, type DropdownOption } from "./components/FintechDropdown";
import { api, type MetricsSummary, type AnalystProfile } from "./services/api";
import type { Verdict } from "./types/generated/verdict.v1";

const ROLE_OPTIONS: DropdownOption[] = [
  {
    value: "L2 Senior Fraud Ops",
    label: "L2 Senior Fraud Ops",
    description: "Full containment, manual override & account unlock authorization.",
  },
  {
    value: "SOC Analyst",
    label: "SOC Analyst",
    description: "Investigation review, evidence correlation & 3DS challenge.",
  },
  {
    value: "Compliance Auditor",
    label: "Compliance Auditor",
    description: "Read-only audit telemetry, policy evaluation & BI export.",
  },
];

export function App(): React.JSX.Element {
  const { selectedTxId, setSelectedTxId } = useUiStore();
  const [activeNavTab, setActiveNavTab] = useState<NavTabId>("feed");
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [cases, setCases] = useState<Verdict[]>([]);
  const [metrics, setMetrics] = useState<MetricsSummary>({
    processed_count: 0,
    allowed_count: 0,
    blocked_count: 0,
    locked_count: 0,
    review_count: 0,
    clean_count: 0,
    fast_path_pct: 100.0,
    avg_latency_ms: 0,
    accuracy_target: "> 99.0%",
    fpr_target: "< 1.0%",
    last_eval_status: "ACTIVE",
    total_tokens_consumed: 0,
    total_cost_usd: 0.0,
    degraded_mode: false,
  });
  const [sseActive, setSseActive] = useState(false);
  const [clearing, setClearing] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const [loadingScenario, setLoadingScenario] = useState<string | null>(null);
  const [populating, setPopulating] = useState(false);

  // Authentication & RBAC Session State (strictly server-side JWT authenticated)
  const [session, setSession] = useState<AnalystProfile | null>(null);
  const [checkingAuth, setCheckingAuth] = useState(true);

  // Verify server-side cryptographic JWT session on initial mount
  useEffect(() => {
    let isMounted = true;
    const verify = async () => {
      try {
        const verified = await api.verifySession();
        if (isMounted) {
          setSession(verified);
        }
      } catch {
        if (isMounted) {
          setSession(null);
        }
      } finally {
        if (isMounted) {
          setCheckingAuth(false);
        }
      }
    };

    verify();

    // Force redirection to login page if any request encounters HTTP 401
    const handleUnauthorized = () => {
      if (isMounted) {
        setSession(null);
      }
    };
    window.addEventListener("aegis:unauthorized", handleUnauthorized);

    return () => {
      isMounted = false;
      window.removeEventListener("aegis:unauthorized", handleUnauthorized);
    };
  }, []);

  const handleRoleChange = (newRole: string) => {
    if (!session) return;
    const updated = { ...session, role: newRole };
    setSession(updated);
    sessionStorage.setItem("aegis_analyst_session", JSON.stringify(updated));
  };

  const handleLogout = async () => {
    try {
      await api.logout();
    } catch {
      // Continue cleanup
    }
    setSession(null);
  };

  const resetLocalState = () => {
    setStreaming(false);
    setCases([]);
    setSelectedTxId(null);
    setMetrics({
      processed_count: 0,
      allowed_count: 0,
      blocked_count: 0,
      locked_count: 0,
      review_count: 0,
      clean_count: 0,
      fast_path_pct: 100.0,
      avg_latency_ms: 0,
      accuracy_target: "> 99.0%",
      fpr_target: "< 1.0%",
      last_eval_status: "ACTIVE",
      total_tokens_consumed: 0,
      total_cost_usd: 0.0,
      degraded_mode: false,
    });
  };

  const handleResetFeed = async () => {
    try {
      setClearing(true);
      await api.clearInvestigations();
      resetLocalState();
    } catch (err) {
      console.error("Failed to clear investigations", err);
    } finally {
      setClearing(false);
    }
  };

  // Interactive Single-Scenario Ingestion Handler
  const handleTriggerScenario = async (
    scenario: "coffee" | "smurfing" | "tor_travel"
  ) => {
    try {
      setLoadingScenario(scenario);
      const res = await api.triggerSimulation(scenario, "sync");
      if (res && "tx_id" in res) {
        const v = res as Verdict;
        setSelectedTxId(v.tx_id);
        setCases((prev) => [v, ...prev.filter((c) => c.tx_id !== v.tx_id)]);
      }
    } catch (err) {
      console.error("Failed to trigger simulation scenario", err);
    } finally {
      setLoadingScenario(null);
    }
  };

  // Populate 3 Representative Benchmark Cases
  const handlePopulateDemoData = async () => {
    try {
      setPopulating(true);
      await api.triggerSimulation("coffee", "sync");
      await new Promise((resolve) => setTimeout(resolve, 350));
      await api.triggerSimulation("smurfing", "sync");
      await new Promise((resolve) => setTimeout(resolve, 350));
      const ato = await api.triggerSimulation("tor_travel", "sync");
      if (ato && "tx_id" in ato) {
        const v = ato as Verdict;
        setSelectedTxId(v.tx_id);
        setCases((prev) => [v, ...prev.filter((c) => c.tx_id !== v.tx_id)]);
      }
    } catch (err) {
      console.error("Failed to populate demo cases", err);
    } finally {
      setPopulating(false);
    }
  };

  const handleToggleStreaming = () => {
    setStreaming((prev) => !prev);
  };

  // Continuous traffic generator when streaming toggle is active
  useEffect(() => {
    if (!streaming || !session) return;

    const sequence: Array<"coffee" | "smurfing" | "tor_travel"> = [
      "coffee",
      "coffee",
      "coffee",
      "smurfing",
      "tor_travel",
    ];
    let idx = 0;

    const timer = setInterval(async () => {
      const scenario = sequence[idx % sequence.length];
      idx++;
      try {
        const res = await api.triggerSimulation(scenario, "sync");
        if (res && "tx_id" in res) {
          const v = res as Verdict;
          setSelectedTxId(v.tx_id);
          setCases((prev) => [v, ...prev.filter((c) => c.tx_id !== v.tx_id)]);
        }
      } catch (err) {
        console.warn("Live stream transaction transient delay:", err);
      }
    }, 3500);

    return () => clearInterval(timer);
  }, [streaming, session, setSelectedTxId]);

  // Ensure an initial case is selected in feed view
  useEffect(() => {
    if (!selectedTxId && cases.length > 0) {
      setSelectedTxId(cases[0].tx_id);
    }
  }, [selectedTxId, cases, setSelectedTxId]);

  // Real-time Gateway Hot-Cache Shield SSE Push Stream + Resilient Polling
  useEffect(() => {
    if (!session) return;
    let isMounted = true;

    // 1. Initial hot-cache fetch
    const fetchInitial = async () => {
      try {
        const [latestCases, latestMetrics] = await Promise.all([
          api.listInvestigations(50),
          api.getMetricsSummary(),
        ]);
        if (isMounted) {
          if (latestCases) {
            setCases(latestCases);
            if (latestCases.length === 0) {
              setSelectedTxId(null);
            }
          }
          if (latestMetrics) {
            setMetrics(latestMetrics);
          }
        }
      } catch {
        // Fall back gracefully when offline or during startup
      }
    };

    fetchInitial();

    // 2. Connect real-time Server-Sent Events push stream (sub-millisecond updates, $0 Firestore reads)
    const unsubscribeSSE = api.subscribeToInvestigationStream(
      (newVerdict: Verdict) => {
        if (!isMounted) return;
        setSseActive(true);
        setCases((prev) => {
          const filtered = prev.filter((c) => c.tx_id !== newVerdict.tx_id);
          return [newVerdict, ...filtered];
        });

        // Optimistically increment live counters in RAM
        setMetrics((prev) => {
          const isAllow = newVerdict.decision === "ALLOW";
          const isBlock = newVerdict.decision === "BLOCK_TX";
          const isLock =
            newVerdict.decision === "LOCK_ACCOUNT" ||
            newVerdict.decision === "DECLINE_LOCKED";
          const isReview = newVerdict.decision === "REVIEW";

          return {
            ...prev,
            processed_count: prev.processed_count + 1,
            allowed_count: (prev.allowed_count ?? prev.clean_count) + (isAllow ? 1 : 0),
            blocked_count: (prev.blocked_count ?? 0) + (isBlock ? 1 : 0),
            locked_count: (prev.locked_count ?? 0) + (isLock ? 1 : 0),
            review_count: (prev.review_count ?? 0) + (isReview ? 1 : 0),
            clean_count: (prev.clean_count ?? 0) + (isAllow ? 1 : 0),
          };
        });
      },
      () => {
        if (isMounted) setSseActive(true);
      },
      () => {
        if (isMounted) setSseActive(false);
      },
      () => {
        if (isMounted) {
          resetLocalState();
        }
      }
    );

    // 3. Low-frequency background sync timer (every 10s) as backup
    const syncInterval = setInterval(fetchInitial, 10000);

    return () => {
      isMounted = false;
      unsubscribeSSE();
      clearInterval(syncInterval);
    };
  }, [session]);

  const currentCase =
    cases.find((c) => c.tx_id === selectedTxId) ?? cases[0] ?? null;

  const handleDecisionRecorded = (updatedVerdict: Verdict) => {
    setCases((prev) =>
      prev.map((c) => (c.tx_id === updatedVerdict.tx_id ? updatedVerdict : c))
    );
  };

  // Escalation count for cases scoring 30-84 or requiring review
  const escalationCount = cases.filter(
    (c) =>
      c.decision === "REVIEW" ||
      c.decision === "CHALLENGE_3DS" ||
      (c.threat_score >= 30 && c.threat_score <= 84)
  ).length;

  // Render session loading splash while verifying JWT token with server
  if (checkingAuth) {
    return (
      <div className="min-h-screen bg-[#070B14] flex flex-col items-center justify-center gap-4 text-white font-sans">
        <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-[#5B4DFB] to-[#4F46E5] flex items-center justify-center shadow-lg shadow-violet-500/25 animate-pulse">
          <Shield className="w-7 h-7 text-white" />
        </div>
        <div className="flex items-center gap-2 text-xs font-mono text-slate-300">
          <span className="w-2 h-2 rounded-full bg-violet-400 animate-ping" />
          <span>Verifying Aegis SOC Cryptographic Session...</span>
        </div>
      </div>
    );
  }

  // Force Login screen if unauthenticated or session key missing/expired
  if (!session) {
    return (
      <LoginModal
        onSuccess={(loginResp) => {
          const profile = loginResp.analyst || loginResp.user!;
          setSession(profile);
        }}
      />
    );
  }

  return (
    <div className="min-h-screen bg-[var(--color-canvas)] text-[var(--color-text-primary)] font-sans flex flex-col selection:bg-[var(--color-brand-violet-subtle)] selection:text-[var(--color-brand-midnight)]">
      {/* ── Top Navigation Bar ──────────────────────────────────────── */}
      <nav className="bg-white/85 backdrop-blur-md border-b border-[var(--color-border)] sticky top-0 z-50 px-4 sm:px-6 lg:px-8 py-3 flex items-center justify-between gap-4">
        {/* Left: Brand Identity */}
        <div className="flex items-center gap-6">
          <div
            onClick={() => setActiveNavTab("feed")}
            className="flex items-center gap-2.5 cursor-pointer group"
          >
            <div className="w-9 h-9 rounded-xl bg-[var(--color-brand-midnight)] flex items-center justify-center text-white shadow-sm transition-transform group-hover:scale-105">
              <Shield className="w-5 h-5 text-violet-300" />
            </div>
            <div className="flex items-baseline gap-1.5">
              <span className="text-xl font-black tracking-tight text-[var(--color-brand-midnight)]">
                aegis
              </span>
              <span className="text-[10px] font-semibold tracking-wider uppercase px-2 py-0.5 rounded-full bg-[var(--color-brand-violet-subtle)] text-[var(--color-brand-violet)]">
                Enterprise SOC
              </span>
            </div>
          </div>
        </div>

        {/* Center: Live Surveillance & SLA Strip */}
        <div className="hidden lg:flex items-center gap-4 text-xs bg-[var(--color-surface-subtle)] px-4 py-1.5 rounded-full border border-[var(--color-border)] shadow-2xs">
          <div className="flex items-center gap-1.5 text-slate-700 font-medium">
            <Activity className="w-3.5 h-3.5 text-emerald-600" />
            <span>Ingestion SLA:</span>
            <span className="font-mono font-bold text-emerald-700">
              &lt; 700ms
            </span>
          </div>
          <span className="text-slate-300">•</span>
          <div className="flex items-center gap-1.5 text-slate-700 font-medium">
            <CheckCircle2 className="w-3.5 h-3.5 text-violet-600" />
            <span>Policy Hard Floors:</span>
            <span className="font-mono font-bold text-[var(--color-brand-midnight)]">
              H1, H2, H3 Active
            </span>
          </div>
          <span className="text-slate-300">•</span>
          <span className="flex items-center gap-1.5 font-mono text-[11px] text-slate-600">
            <span
              className={`w-2 h-2 rounded-full ${
                sseActive ? "bg-emerald-500 animate-pulse" : "bg-cyan-500"
              }`}
            />
            <span className="font-semibold">
              {sseActive ? "SSE Live Stream" : "Gateway Shield"}
            </span>
          </span>
        </div>

        {/* Right: Controls & RBAC Role Switcher */}
        <div className="flex items-center gap-3">
          {/* Reset Feed Button */}
          <button
            type="button"
            onClick={handleResetFeed}
            disabled={clearing}
            title="Clear past transactions and reset the dashboard to fresh state"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 hover:text-slate-900 transition-all cursor-pointer shadow-2xs disabled:opacity-50"
          >
            <RotateCcw
              className={`w-3.5 h-3.5 text-slate-500 ${clearing ? "animate-spin" : ""}`}
            />
            <span className="hidden sm:inline">{clearing ? "Clearing..." : "Reset Feed"}</span>
          </button>

          {/* RBAC Role Switcher (Custom Fintech Dropdown) */}
          <div className="flex items-center gap-2 bg-slate-50 border border-slate-200 rounded-full px-2.5 py-1">
            <div className="w-6 h-6 rounded-full bg-violet-100 text-violet-700 font-bold text-[11px] flex items-center justify-center">
              {session.name.charAt(0).toUpperCase()}
            </div>
            <span className="text-[11px] font-bold text-[var(--color-brand-midnight)] leading-tight hidden sm:inline">
              {session.name}
            </span>
            <FintechDropdown
              value={session.role}
              onChange={handleRoleChange}
              options={ROLE_OPTIONS}
            />
          </div>

          {/* Logout Action */}
          <button
            type="button"
            onClick={handleLogout}
            title="Log out of Aegis SOC"
            className="w-8 h-8 rounded-full border border-slate-200 bg-white hover:bg-rose-50 hover:text-rose-600 text-slate-500 flex items-center justify-center transition-colors cursor-pointer"
          >
            <LogOut className="w-3.5 h-3.5" />
          </button>
        </div>
      </nav>

      {/* ── Main Application Workspace with Collapsible Sidebar ──────── */}
      <div className="flex-1 max-w-[1720px] w-full mx-auto p-4 sm:p-6 lg:p-8 flex gap-6 items-start">
        {/* Navigation Sidebar */}
        <NavigationSidebar
          activeTab={activeNavTab}
          onTabChange={setActiveNavTab}
          escalationCount={escalationCount}
          collapsed={sidebarCollapsed}
          onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
        />

        {/* Dynamic Content Views */}
        <div className="flex-1 min-w-0 flex flex-col gap-6">
          {/* TAB 1: Real-time Ingestion & Threat Feed */}
          {activeNavTab === "feed" && (
            <>
              {/* Hero & Command Simulator Bar */}
              <section className="bg-white rounded-[28px] border border-[var(--color-border)] shadow-[var(--shadow-floating)] p-6 lg:p-8">
                <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 pb-6 border-b border-[var(--color-border)]">
                  <div className="max-w-2xl">
                    <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[var(--color-brand-midnight)] text-white text-xs font-medium mb-3">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                      <span>Real-Time Fraud Prevention System</span>
                    </div>
                    <h1 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold tracking-tight text-[var(--color-brand-midnight)] leading-tight mb-2">
                      One platform. Zero transaction delay.
                    </h1>
                    <p className="text-sm text-[var(--color-text-secondary)] leading-relaxed">
                      Enterprise transaction fraud surveillance powered by deterministic banking policy guardrails and multi-vector correlation to neutralize threats with sub-second latency.
                    </p>
                  </div>

                  {/* Real-Time Operational Counters */}
                  <div className="flex flex-wrap items-center gap-3">
                    <div className="bg-[var(--color-surface-subtle)] border border-[var(--color-border)] rounded-2xl px-4 py-3 flex flex-col items-start min-w-[125px]">
                      <div className="flex items-center gap-1.5">
                        <span className="w-2 h-2 rounded-full bg-violet-600 animate-pulse" />
                        <span className="text-xl font-bold text-[var(--color-brand-midnight)] font-mono">
                          {metrics.processed_count.toLocaleString()}
                        </span>
                      </div>
                      <span className="text-[11px] text-[var(--color-text-secondary)] font-medium">
                        Total Ingested
                      </span>
                    </div>

                    <div className="bg-emerald-50/60 border border-emerald-200/60 rounded-2xl px-4 py-3 flex flex-col items-start min-w-[125px]">
                      <span className="text-xl font-bold text-emerald-700 font-mono">
                        {(metrics.allowed_count ?? metrics.clean_count).toLocaleString()}
                      </span>
                      <span className="text-[11px] text-emerald-800 font-medium">
                        Allowed (Clean)
                      </span>
                    </div>

                    <div className="bg-rose-50/60 border border-rose-200/60 rounded-2xl px-4 py-3 flex flex-col items-start min-w-[125px]">
                      <span className="text-xl font-bold text-rose-700 font-mono">
                        {(
                          (metrics.blocked_count || 0) +
                          (metrics.locked_count || 0)
                        ).toLocaleString()}
                      </span>
                      <span className="text-[11px] text-rose-800 font-medium">
                        Fraud Neutralized
                      </span>
                    </div>

                    <div className="bg-[var(--color-surface-subtle)] border border-[var(--color-border)] rounded-2xl px-4 py-3 flex flex-col items-start min-w-[110px]">
                      <span className="text-xl font-bold text-[var(--color-brand-terracotta)] font-mono">
                        {metrics.avg_latency_ms}ms
                      </span>
                      <span className="text-[11px] text-[var(--color-text-secondary)] font-medium">
                        Avg Latency
                      </span>
                    </div>

                    <div className="bg-[var(--color-surface-subtle)] border border-[var(--color-border)] rounded-2xl px-4 py-3 flex flex-col items-start min-w-[110px]">
                      <span className="text-xl font-bold text-violet-700 font-mono">
                        {metrics.fast_path_pct ?? 98.4}%
                      </span>
                      <span className="text-[11px] text-[var(--color-text-secondary)] font-medium">
                        Fast-Path Triage
                      </span>
                    </div>
                  </div>
                </div>

                {/* Preloaded Core Banking Channels & Pipeline Surveillance */}
                <SimulationBar
                  onTriggerScenario={handleTriggerScenario}
                  loadingScenario={loadingScenario}
                  streaming={streaming}
                  onToggleStreaming={handleToggleStreaming}
                  onPopulateDemoData={handlePopulateDemoData}
                  populating={populating}
                />
              </section>

              {/* ── Two-Column Operational Surface (Feed & Investigation) ─── */}
              <section className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                {/* Left Column: Transaction Feed (5 Cols) */}
                <div className="lg:col-span-5">
                  <TransactionFeed
                    cases={cases}
                    onSelectCase={(txId) => setSelectedTxId(txId)}
                  />
                </div>

                {/* Right Column: Case Investigation & Reasoning Terminal (7 Cols) */}
                <div className="lg:col-span-7 flex flex-col gap-4">
                  <div className="flex items-center justify-between px-2">
                    <span className="text-xs font-bold uppercase tracking-wider text-[var(--color-text-secondary)] flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full bg-[var(--color-brand-terracotta)]" />
                      Case Investigation Terminal
                    </span>
                    <span className="text-xs font-mono text-[var(--color-text-muted)]">
                      Active ID: {currentCase?.tx_id ?? "None"}
                    </span>
                  </div>

                  <div className="bg-white rounded-[28px] border border-[var(--color-border)] shadow-[var(--shadow-floating)] p-6 lg:p-8 flex flex-col gap-6">
                    {currentCase ? (
                      <>
                        {/* Account Lockout Banner */}
                        <LockBanner
                          verdict={currentCase}
                          onUnlockClick={() => {
                            api
                              .recordAnalystDecision(
                                currentCase.tx_id,
                                "UNLOCK",
                                "Analyst manual release: Customer identity confirmed."
                              )
                              .then(handleDecisionRecorded)
                              .catch(() => {});
                          }}
                        />

                        {/* Top 2-Column Gauge & Verdict Summary */}
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                          <ThreatGauge
                            score={currentCase.threat_score}
                            riskLevel={currentCase.risk_level}
                            hardFloor={currentCase.score_breakdown?.floor ?? 0}
                          />

                          <div className="p-5 rounded-2xl bg-[var(--color-surface-subtle)] border border-[var(--color-border)] flex flex-col justify-between">
                            <div className="flex items-center justify-between mb-3">
                              <div className="w-10 h-10 rounded-xl bg-white text-violet-600 flex items-center justify-center shadow-xs border border-violet-100">
                                <Lock className="w-5 h-5 text-rose-600" />
                              </div>
                              <span className="text-xs font-mono font-bold px-2.5 py-1 rounded-full border bg-white text-[var(--color-brand-midnight)] border-[var(--color-border)]">
                                {currentCase.decision}
                              </span>
                            </div>
                            <div>
                              <h3 className="text-xs font-bold uppercase tracking-wider text-[var(--color-brand-midnight)]">
                                Automated Policy Decision
                              </h3>
                              <p className="text-[11px] text-[var(--color-text-secondary)] mt-1 leading-relaxed">
                                Enforced by banking risk thresholds with strict guardrails and audited customer safety containment.
                              </p>
                            </div>
                          </div>
                        </div>

                        {/* Multi-Vector Decision Telemetry */}
                        <AgentChatLog verdict={currentCase} />

                        {/* Analyst Manual Override & Audit Trail */}
                        <AnalystActions
                          verdict={currentCase}
                          onDecisionRecorded={handleDecisionRecorded}
                        />
                      </>
                    ) : (
                      <div className="py-20 px-6 text-center flex flex-col items-center justify-center gap-4">
                        <div className="w-16 h-16 rounded-3xl bg-[var(--color-brand-violet-subtle)] text-[var(--color-brand-violet)] flex items-center justify-center shadow-inner">
                          <Shield className="w-8 h-8 animate-pulse text-violet-600" />
                        </div>
                        <div className="max-w-md">
                          <h3 className="text-base font-bold text-[var(--color-brand-midnight)]">
                            Operational Standby: Gateway Stream Active
                          </h3>
                          <p className="text-xs text-[var(--color-text-secondary)] mt-1.5 leading-relaxed">
                            Preloaded banking channels are online and listening on port 8080. Live transaction investigations will appear here in real time.
                          </p>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </section>
            </>
          )}

          {/* TAB 2: Case Queue & Escalations Workbench */}
          {activeNavTab === "queue" && (
            <CaseQueueView
              cases={cases}
              onDecisionRecorded={handleDecisionRecorded}
              userRole={session.role}
            />
          )}

          {/* TAB 3: Risk Policy Engine & Guardrails */}
          {activeNavTab === "policies" && <PolicyEngineView />}

          {/* TAB 4: Analytics & Executive BI Dashboard */}
          {activeNavTab === "analytics" && (
            <AnalyticsView cases={cases} metrics={metrics} />
          )}

          {/* TAB 5: API Quotas, Token Burn & Rate Limits */}
          {activeNavTab === "quotas" && <ApiQuotaView metrics={metrics} />}

          {/* ── System Status & Operational Indicators Footer ──────────── */}
          <footer className="bg-white rounded-[28px] border border-[var(--color-border)] shadow-[var(--shadow-floating)] p-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-[var(--color-text-secondary)]">
            <div className="flex items-center gap-3">
              <span className="flex items-center gap-1.5 font-semibold text-[var(--color-brand-midnight)]">
                <Radio className="w-4 h-4 text-emerald-500 animate-pulse" />
                <span>Aegis Real-Time Protection Active</span>
              </span>
              <span className="text-slate-300">•</span>
              <span>
                Target Accuracy:{" "}
                <strong className="text-[var(--color-brand-midnight)]">
                  {metrics.accuracy_target}
                </strong>
              </span>
              <span className="text-slate-300">•</span>
              <span>
                FPR Target:{" "}
                <strong className="text-[var(--color-brand-midnight)]">
                  {metrics.fpr_target}
                </strong>
              </span>
            </div>
            <div className="flex items-center gap-2 font-mono text-[11px] text-[var(--color-text-muted)]">
              <Layers className="w-3.5 h-3.5 text-violet-500" />
              <span>Aegis Enterprise Fraud Defense • Real-Time Engine Active</span>
            </div>
          </footer>
        </div>
      </div>
    </div>
  );
}

export default App;
