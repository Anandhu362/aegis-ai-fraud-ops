import React from "react";
import {
  Radio,
  FileCheck2,
  ShieldAlert,
  BarChart3,
  Cpu,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";

export type NavTabId = "feed" | "queue" | "policies" | "analytics" | "quotas";

interface NavigationSidebarProps {
  activeTab: NavTabId;
  onTabChange: (tab: NavTabId) => void;
  escalationCount: number;
  collapsed: boolean;
  onToggleCollapse: () => void;
}

export function NavigationSidebar({
  activeTab,
  onTabChange,
  escalationCount,
  collapsed,
  onToggleCollapse,
}: NavigationSidebarProps): React.JSX.Element {
  const navItems = [
    {
      id: "feed" as NavTabId,
      label: "Live Transaction Stream",
      icon: Radio,
      badge: null,
    },
    {
      id: "queue" as NavTabId,
      label: "Escalations & Case Queue",
      icon: FileCheck2,
      badge: escalationCount > 0 ? escalationCount : null,
    },
    {
      id: "policies" as NavTabId,
      label: "Banking Policies & Hard Floors",
      icon: ShieldAlert,
      badge: null,
    },
    {
      id: "analytics" as NavTabId,
      label: "Operations Analytics & BI",
      icon: BarChart3,
      badge: null,
    },
    {
      id: "quotas" as NavTabId,
      label: "System Capacity & Rate Limits",
      icon: Cpu,
      badge: null,
    },
  ];

  return (
    <aside
      className={`bg-white rounded-[24px] border border-[var(--color-border)] shadow-[var(--shadow-card)] p-3 flex flex-col justify-between transition-all duration-300 shrink-0 ${
        collapsed ? "w-16" : "w-64"
      }`}
    >
      <div className="flex flex-col gap-2">
        {/* Toggle Button */}
        <div className="flex items-center justify-between pb-2 mb-1 border-b border-[var(--color-border)] px-1">
          {!collapsed && (
            <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted)] font-mono">
              SOC Navigation
            </span>
          )}
          <button
            type="button"
            onClick={onToggleCollapse}
            title={collapsed ? "Expand Sidebar" : "Collapse Sidebar"}
            className="p-1.5 rounded-xl hover:bg-slate-100 text-slate-500 transition-colors cursor-pointer ml-auto"
          >
            {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>

        {/* Navigation Items */}
        <div className="flex flex-col gap-1.5">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;

            return (
              <button
                key={item.id}
                type="button"
                onClick={() => onTabChange(item.id)}
                title={collapsed ? item.label : undefined}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-semibold transition-all cursor-pointer text-left ${
                  isActive
                    ? "bg-[var(--color-brand-midnight)] text-white shadow-sm"
                    : "text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-subtle)] hover:text-[var(--color-brand-midnight)]"
                }`}
              >
                <Icon
                  className={`w-4 h-4 shrink-0 ${
                    isActive ? "text-violet-300" : "text-slate-500"
                  }`}
                />
                {!collapsed && (
                  <span className="flex-1 truncate tracking-tight">{item.label}</span>
                )}
                {!collapsed && item.badge !== null && (
                  <span
                    className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded-full ${
                      isActive
                        ? "bg-violet-700 text-white"
                        : "bg-amber-100 text-amber-800"
                    }`}
                  >
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Footer Info in Sidebar */}
      {!collapsed && (
        <div className="p-3 rounded-2xl bg-[var(--color-surface-subtle)] border border-[var(--color-border)] mt-4">
          <div className="flex items-center gap-2 mb-1">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-[11px] font-bold text-[var(--color-brand-midnight)]">
              Real-Time Engine Active
            </span>
          </div>
          <p className="text-[10px] text-[var(--color-text-muted)] leading-relaxed">
            Multi-vector cognitive defense guarding digital banking channels with zero friction.
          </p>
        </div>
      )}
    </aside>
  );
}
