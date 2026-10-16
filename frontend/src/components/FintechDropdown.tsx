import React, { useState, useRef, useEffect } from "react";
import { ChevronDown, Check, Shield } from "lucide-react";

export interface DropdownOption {
  value: string;
  label: string;
  description?: string;
  badge?: string;
}

interface FintechDropdownProps {
  value: string;
  onChange: (value: string) => void;
  options: DropdownOption[];
  label?: string;
  className?: string;
}

export function FintechDropdown({
  value,
  onChange,
  options,
  label,
  className = "",
}: FintechDropdownProps): React.JSX.Element {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const selectedOption = options.find((opt) => opt.value === value) || options[0];

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div ref={containerRef} className={`relative inline-block text-left ${className}`}>
      {label && (
        <label className="block text-[11px] font-bold text-slate-700 uppercase tracking-wider mb-1.5 font-mono">
          {label}
        </label>
      )}

      {/* Trigger Button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center justify-between gap-2.5 px-3 py-1.5 rounded-full bg-slate-50 hover:bg-slate-100/80 border border-slate-200 text-slate-800 text-xs font-semibold shadow-2xs hover:border-slate-300 transition-all cursor-pointer focus:outline-none focus:ring-2 focus:ring-violet-500/20"
        aria-haspopup="listbox"
        aria-expanded={isOpen}
      >
        <div className="flex items-center gap-1.5 text-left">
          <Shield className="w-3.5 h-3.5 text-violet-600 shrink-0" />
          <span className="font-semibold text-[11px] text-slate-900 leading-tight">
            {selectedOption?.label || value}
          </span>
        </div>
        <ChevronDown
          className={`w-3.5 h-3.5 text-slate-500 transition-transform duration-200 ${
            isOpen ? "rotate-180 text-violet-600" : ""
          }`}
        />
      </button>

      {/* Floating Menu Card */}
      {isOpen && (
        <div className="absolute right-0 mt-1.5 w-72 rounded-2xl bg-white border border-slate-200 shadow-xl z-50 overflow-hidden animate-in fade-in zoom-in-95 duration-150">
          <div className="px-3 py-2 bg-slate-50 border-b border-slate-100 flex items-center justify-between">
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-500">
              Select Security Role
            </span>
            <span className="text-[10px] font-mono text-violet-700 font-bold bg-violet-50 px-1.5 py-0.5 rounded border border-violet-200/60">
              RBAC
            </span>
          </div>

          <div className="p-1.5 flex flex-col gap-1 max-h-64 overflow-y-auto" role="listbox">
            {options.map((option) => {
              const isSelected = option.value === value;
              return (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => {
                    onChange(option.value);
                    setIsOpen(false);
                  }}
                  className={`w-full text-left px-3 py-2.5 rounded-xl text-xs flex items-start justify-between gap-2 transition-colors cursor-pointer ${
                    isSelected
                      ? "bg-violet-50/80 text-violet-900 font-semibold"
                      : "text-slate-700 hover:bg-slate-50 hover:text-slate-900"
                  }`}
                  role="option"
                  aria-selected={isSelected}
                >
                  <div className="flex flex-col gap-0.5">
                    <span className="font-bold text-[12px]">{option.label}</span>
                    {option.description && (
                      <span className="text-[10px] text-slate-500 leading-tight font-normal">
                        {option.description}
                      </span>
                    )}
                  </div>
                  {isSelected && (
                    <Check className="w-4 h-4 text-violet-600 shrink-0 mt-0.5" />
                  )}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
export default FintechDropdown;
