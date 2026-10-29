import React, { useState } from 'react';
import { ShieldCheck, Lock, User, ArrowRight, AlertCircle, Sparkles, KeyRound } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function LoginPage() {
  const { login } = useAuth();
  const [username, setUsername] = useState('agency_admin');
  const [password, setPassword] = useState('AdminPass123!');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(username, password);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const loginAsDemoRole = async (userVal, passVal) => {
    setError(null);
    setLoading(true);
    try {
      await login(userVal, passVal);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#070B14] text-slate-100 flex flex-col justify-center items-center p-6 selection:bg-violet-600 selection:text-white">
      {/* Background Glow */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[550px] h-[550px] bg-violet-600/10 rounded-full blur-[130px] pointer-events-none"></div>

      <div className="w-full max-w-md relative z-10 space-y-6">
        {/* Brand Header */}
        <div className="text-center space-y-2">
          <div className="inline-flex h-12 w-12 rounded-2xl bg-gradient-to-tr from-violet-600 to-cyan-500 p-0.5 shadow-xl shadow-violet-500/20">
            <div className="h-full w-full bg-[#070B14] rounded-[14px] flex items-center justify-center">
              <ShieldCheck className="w-6 h-6 text-cyan-400" />
            </div>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Inkloom Guardian</h1>
          <p className="text-xs text-slate-400">Evidence-Led Brand Governance & Content Trust Platform</p>
        </div>

        {/* Login Card */}
        <div className="rounded-2xl border border-slate-800/90 bg-[#0D1527]/90 backdrop-blur-xl p-8 shadow-2xl space-y-6">
          <div className="space-y-1">
            <h2 className="text-lg font-semibold text-white">Sign In to Workspace</h2>
            <p className="text-xs text-slate-400">Enter your credentials or choose a pre-configured demo role below.</p>
          </div>

          {error && (
            <div className="p-3.5 rounded-lg bg-red-950/40 border border-red-800/60 flex items-start space-x-2.5 text-xs text-red-300">
              <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-slate-300">Username</label>
              <div className="relative">
                <User className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 text-sm rounded-lg bg-slate-900/90 border border-slate-700/80 text-white placeholder-slate-500 focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500 transition"
                  placeholder="Enter username"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-medium text-slate-300">Password</label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 text-sm rounded-lg bg-slate-900/90 border border-slate-700/80 text-white placeholder-slate-500 focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500 transition"
                  placeholder="••••••••••••"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white font-medium text-sm shadow-lg shadow-violet-600/30 transition flex items-center justify-center space-x-2 cursor-pointer disabled:opacity-50"
            >
              <span>{loading ? 'Authenticating...' : 'Sign In'}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          {/* Quick Demo Role Selector */}
          <div className="pt-4 border-t border-slate-800/80 space-y-2.5">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 flex items-center space-x-1.5">
                <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
                <span>Quick Login As (Demo Roles)</span>
              </span>
            </div>

            <div className="grid grid-cols-2 gap-2 text-xs">
              <button
                type="button"
                onClick={() => loginAsDemoRole('agency_admin', 'AdminPass123!')}
                disabled={loading}
                className="p-2 rounded-lg border border-slate-800 bg-slate-900/60 hover:border-violet-500/50 hover:bg-violet-950/20 text-left transition cursor-pointer disabled:opacity-50"
              >
                <div className="font-semibold text-cyan-400">Agency Admin</div>
                <div className="text-[10px] text-slate-500">Manage rules & sources</div>
              </button>

              <button
                type="button"
                onClick={() => loginAsDemoRole('brand_reviewer', 'ReviewerPass123!')}
                disabled={loading}
                className="p-2 rounded-lg border border-slate-800 bg-slate-900/60 hover:border-emerald-500/50 hover:bg-emerald-950/20 text-left transition cursor-pointer disabled:opacity-50"
              >
                <div className="font-semibold text-emerald-400">Brand Reviewer</div>
                <div className="text-[10px] text-slate-500">Approve / Reject versions</div>
              </button>

              <button
                type="button"
                onClick={() => loginAsDemoRole('content_creator', 'CreatorPass123!')}
                disabled={loading}
                className="p-2 rounded-lg border border-slate-800 bg-slate-900/60 hover:border-violet-500/50 hover:bg-violet-950/20 text-left transition cursor-pointer disabled:opacity-50"
              >
                <div className="font-semibold text-violet-400">Content Creator</div>
                <div className="text-[10px] text-slate-500">Submit copy & revisions</div>
              </button>

              <button
                type="button"
                onClick={() => loginAsDemoRole('account_manager', 'ManagerPass123!')}
                disabled={loading}
                className="p-2 rounded-lg border border-slate-800 bg-slate-900/60 hover:border-indigo-500/50 hover:bg-indigo-950/20 text-left transition cursor-pointer disabled:opacity-50"
              >
                <div className="font-semibold text-indigo-400">Account Manager</div>
                <div className="text-[10px] text-slate-500">Coordinate reviews</div>
              </button>
            </div>
          </div>
        </div>

        {/* Security Notice */}
        <p className="text-center text-[11px] text-slate-500">
          Server-side RBAC and tenant isolation are enforced on every API request.
        </p>
      </div>
    </div>
  );
}
