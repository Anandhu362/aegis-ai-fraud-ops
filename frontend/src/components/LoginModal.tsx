import React, { useState } from "react";
import {
  Shield,
  Lock,
  Mail,
  ArrowRight,
  Loader2,
  Eye,
  EyeOff,
  AlertCircle,
  ShieldCheck,
  Activity,
  KeyRound,
} from "lucide-react";
import { api, type LoginResponse } from "../services/api";

interface LoginModalProps {
  onSuccess: (session: LoginResponse) => void;
}

export function LoginModal({ onSuccess }: LoginModalProps): React.JSX.Element {
  const [email, setEmail] = useState("demo@aegis.com");
  const [password, setPassword] = useState("password");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      // Server-side authentication: credentials validated on server, issuing an HMAC-SHA256 JWT
      const resp = await api.login(email, password, "L2 Senior Fraud Ops");
      onSuccess(resp);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Authentication failed";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleFillDemo = () => {
    setEmail("demo@aegis.com");
    setPassword("password");
    setError(null);
  };

  return (
    <div className="fixed inset-0 z-50 w-screen h-screen flex flex-col lg:flex-row bg-white overflow-hidden font-sans">
      {/* ── Left Column: Enterprise Brand & Banking Integrity Hero ─────── */}
      <div className="w-full lg:w-[45%] h-auto lg:h-full bg-gradient-to-br from-[#4338CA] via-[#4F46E5] to-[#312E81] text-white p-8 sm:p-12 lg:p-16 flex flex-col justify-between relative overflow-hidden shrink-0">
        {/* Subtle Architectural Lighting */}
        <div className="absolute -bottom-24 -right-24 w-80 h-80 bg-white/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -top-16 -left-16 w-64 h-64 bg-indigo-300/15 rounded-full blur-2xl pointer-events-none" />

        {/* Top Header Identity */}
        <div className="relative z-10 flex items-center gap-3">
          <div className="w-11 h-11 rounded-2xl bg-white/15 backdrop-blur-md flex items-center justify-center border border-white/20 text-white shadow-sm">
            <Shield className="w-6 h-6 text-white" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-black tracking-tight text-white">
              aegis
            </span>
            <span className="text-[10px] font-bold tracking-wider uppercase px-2.5 py-0.5 rounded-full bg-white/15 text-white border border-white/20">
              Fraud Ops
            </span>
          </div>
        </div>

        {/* Center Enterprise Banking Core Message */}
        <div className="relative z-10 my-8 lg:my-auto max-w-lg">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 backdrop-blur-sm border border-white/15 text-[11px] font-semibold text-white/90 mb-4 font-mono">
            <Activity className="w-3.5 h-3.5 text-emerald-300" />
            <span>High-Throughput Banking Platform</span>
          </div>
          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-black tracking-tight text-white leading-tight">
            Transaction Integrity & Fraud Prevention
          </h1>
          <p className="text-sm sm:text-base text-white/85 mt-4 leading-relaxed font-normal">
            Enterprise Banking Security Operations Center. Real-time transaction surveillance, deterministic risk guardrails, and automated containment for digital payment rails.
          </p>

          {/* Institutional Banking Guarantees */}
          <div className="flex flex-col gap-3 mt-8">
            <div className="flex items-center gap-3 text-xs text-white/90 bg-white/10 backdrop-blur-sm px-4 py-2.5 rounded-2xl border border-white/15">
              <ShieldCheck className="w-4 h-4 text-emerald-300 shrink-0" />
              <span className="font-semibold">&lt; 700ms Deterministic Fast-Path Verification</span>
            </div>
            <div className="flex items-center gap-3 text-xs text-white/90 bg-white/10 backdrop-blur-sm px-4 py-2.5 rounded-2xl border border-white/15">
              <Lock className="w-4 h-4 text-cyan-300 shrink-0" />
              <span className="font-semibold">Enforced BSA/AML Policy Hard Floors (H1, H2, H3)</span>
            </div>
            <div className="flex items-center gap-3 text-xs text-white/90 bg-white/10 backdrop-blur-sm px-4 py-2.5 rounded-2xl border border-white/15">
              <Activity className="w-4 h-4 text-indigo-200 shrink-0" />
              <span className="font-semibold">FIPS &amp; ISO 20022 Financial Standards Compliance</span>
            </div>
          </div>
        </div>

        {/* Bottom Platform Compliance Notice */}
        <div className="relative z-10 pt-6 border-t border-white/15 flex items-center justify-between text-[11px] text-white/70 font-mono">
          <span>Aegis Enterprise Banking Infrastructure</span>
          <span>Cryptographic JWT • HS256</span>
        </div>
      </div>

      {/* ── Right Column: Clean Enterprise Login Form ───────────────── */}
      <div className="w-full lg:w-[55%] h-full bg-white p-8 sm:p-12 lg:p-20 flex flex-col justify-center items-center overflow-y-auto">
        <div className="max-w-md w-full flex flex-col gap-6">
          {/* Form Header */}
          <div className="text-left">
            <h2 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
              Welcome Back
            </h2>
            <p className="text-xs sm:text-sm text-slate-500 mt-1.5 leading-relaxed">
              Enter your credentials to access the Aegis SOC analyst terminal.
            </p>
          </div>

          {/* Error Notification Alert */}
          {error && (
            <div className="p-3.5 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-start gap-2.5">
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
              <div>
                <span className="font-bold">Authentication Failed:</span> {error}
              </div>
            </div>
          )}

          {/* Credentials Form */}
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            {/* Corporate Email Field */}
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-bold text-slate-700">
                Analyst Email / Corporate ID
              </label>
              <div className="relative">
                <Mail className="absolute left-4 top-3.5 w-4 h-4 text-slate-400" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="demo@aegis.com"
                  className="w-full pl-11 pr-4 py-3 bg-slate-50 border border-slate-200 rounded-2xl text-xs sm:text-sm font-medium text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-violet-500/25 focus:border-violet-600 focus:bg-white transition-all"
                />
              </div>
            </div>

            {/* Password Field */}
            <div className="flex flex-col gap-1.5">
              <div className="flex items-center justify-between">
                <label className="text-xs font-bold text-slate-700">
                  Password
                </label>
                <button
                  type="button"
                  onClick={handleFillDemo}
                  className="text-[11px] font-semibold text-violet-600 hover:text-violet-700 transition-colors cursor-pointer"
                >
                  Forgot Password?
                </button>
              </div>
              <div className="relative">
                <Lock className="absolute left-4 top-3.5 w-4 h-4 text-slate-400" />
                <input
                  type={showPassword ? "text" : "password"}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full pl-11 pr-11 py-3 bg-slate-50 border border-slate-200 rounded-2xl text-xs sm:text-sm font-medium text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-violet-500/25 focus:border-violet-600 focus:bg-white transition-all"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3.5 top-3.5 text-slate-400 hover:text-slate-600 cursor-pointer"
                  title={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? (
                    <EyeOff className="w-4 h-4" />
                  ) : (
                    <Eye className="w-4 h-4" />
                  )}
                </button>
              </div>
            </div>

            {/* Submit Action Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full mt-2 py-3.5 px-6 rounded-2xl bg-[#4F46E5] hover:bg-[#4338CA] text-white font-bold text-sm shadow-md hover:shadow-lg transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Verifying Session...</span>
                </>
              ) : (
                <>
                  <span>Sign In to SOC Terminal</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* OR Divider */}
          <div className="relative my-1">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-slate-200" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-white px-3 text-slate-400 font-semibold tracking-wider text-[10px]">
                Pre-configured Access
              </span>
            </div>
          </div>

          {/* Authorized Demo Credentials Helper */}
          <button
            type="button"
            onClick={handleFillDemo}
            className="w-full py-2.5 px-4 rounded-2xl bg-slate-50 hover:bg-slate-100 text-slate-700 border border-slate-200 text-xs font-semibold flex items-center justify-center gap-2 transition-all cursor-pointer shadow-2xs hover:shadow-xs"
          >
            <KeyRound className="w-3.5 h-3.5 text-violet-600" />
            <span>Pre-fill Authorized Analyst (demo@aegis.com / password)</span>
          </button>

          {/* Footer Security Footnote */}
          <p className="text-[11px] text-center text-slate-400 font-mono mt-2">
            Protected by Cryptographic JWT • 256-Bit HMAC Security
          </p>
        </div>
      </div>
    </div>
  );
}

export default LoginModal;
