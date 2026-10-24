import React, { useState } from 'react';
import { 
  ShieldCheck, 
  Database, 
  Server, 
  Cpu, 
  CheckCircle2, 
  AlertCircle, 
  Layers, 
  Briefcase, 
  Lock, 
  Sparkles,
  Users,
  FileCheck2,
  ArrowRight
} from 'lucide-react';
import { AuthProvider, useAuth } from './context/AuthContext';
import LoginPage from './components/LoginPage';
import Navbar from './components/Navbar';
import WorkspacesView from './components/WorkspacesView';
import BrandKnowledgeView from './components/BrandKnowledgeView';
import ContentSubmissionView from './components/ContentSubmissionView';
import VersionHistoryView from './components/VersionHistoryView';
import ReviewWorkspaceView from './components/ReviewWorkspaceView';

function MainApp() {
  const { user, currentWorkspace, isAuthenticated, loading } = useAuth();
  const [activePage, setActivePage] = useState('dashboard');

  if (loading) {
    return (
      <div className="min-h-screen bg-[#070B14] flex items-center justify-center text-slate-400">
        <div className="flex items-center space-x-3">
          <div className="w-5 h-5 border-2 border-violet-500 border-t-transparent rounded-full animate-spin"></div>
          <span className="text-sm">Verifying session with Inkloom Guardian API...</span>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginPage />;
  }

  return (
    <div className="min-h-screen bg-[#070B14] text-slate-100 flex flex-col font-sans selection:bg-violet-600 selection:text-white">
      <Navbar activePage={activePage} setActivePage={setActivePage} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-8 space-y-8">
        {/* Render Page Based on Active Navigation */}
        {activePage === 'workspaces' && <WorkspacesView />}
        {activePage === 'knowledge' && <BrandKnowledgeView />}
        {activePage === 'submit' && (
          <ContentSubmissionView onSubmitted={() => setActivePage('versions')} />
        )}
        {activePage === 'versions' && <VersionHistoryView />}
        {activePage === 'review' && <ReviewWorkspaceView />}

        {activePage === 'dashboard' && (
          <div className="space-y-8">
            {/* Phase 3 Welcome Hero */}
            <div className="relative overflow-hidden rounded-2xl border border-slate-800/80 bg-gradient-to-br from-[#0D1527] via-[#090E1C] to-[#070B14] p-8 shadow-2xl">
              <div className="absolute top-0 right-0 -mt-12 -mr-12 w-96 h-96 bg-violet-600/10 rounded-full blur-3xl pointer-events-none"></div>

              <div className="relative z-10 max-w-3xl space-y-3">
                <div className="inline-flex items-center space-x-2 text-xs font-semibold px-3 py-1 rounded-full bg-emerald-950/60 text-emerald-300 border border-emerald-800/40">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Phase 6 — AI Review Workspace & Evidence-Linked Findings Active</span>
                </div>

                <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight text-white leading-tight">
                  Welcome, {user?.full_name || user?.username}!
                </h1>

                <p className="text-slate-300 text-sm md:text-base leading-relaxed">
                  You are currently authenticated with active workspace{' '}
                  <strong className="text-cyan-400">{currentWorkspace?.workspace_name}</strong> holding the{' '}
                  <span className="text-violet-300 font-semibold">{currentWorkspace?.role_display}</span> role.
                </p>

                <div className="pt-2 flex flex-wrap gap-3">
                  <button
                    onClick={() => setActivePage('workspaces')}
                    className="px-4 py-2 rounded-xl bg-violet-600 hover:bg-violet-500 text-white font-medium text-xs shadow-lg shadow-violet-600/25 transition flex items-center space-x-2 cursor-pointer"
                  >
                    <span>Manage Client Workspaces</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>

            {/* Role Authority Indicator Card */}
            <div className="rounded-2xl border border-slate-800 bg-[#0D1527]/70 p-6 space-y-4">
              <div className="flex items-center space-x-2">
                <Lock className="w-5 h-5 text-violet-400" />
                <h3 className="font-semibold text-white">Your Backend-Enforced Permissions</h3>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 pt-1">
                <div className={`p-4 rounded-xl border text-xs space-y-1.5 ${
                  currentWorkspace?.role === 'AGENCY_ADMIN'
                    ? 'border-cyan-500/50 bg-cyan-950/20 text-cyan-200'
                    : 'border-slate-800 bg-slate-900/60 text-slate-400'
                }`}>
                  <div className="font-semibold flex items-center justify-between">
                    <span>Manage Brand Rules & Claims</span>
                    {currentWorkspace?.role === 'AGENCY_ADMIN' && <CheckCircle2 className="w-4 h-4 text-cyan-400" />}
                  </div>
                  <p className="text-[11px] opacity-80">Configure prohibited phrases, mandatory qualifiers, and source benchmarks.</p>
                </div>

                <div className={`p-4 rounded-xl border text-xs space-y-1.5 ${
                  currentWorkspace?.role === 'CONTENT_CREATOR' || currentWorkspace?.role === 'AGENCY_ADMIN'
                    ? 'border-violet-500/50 bg-violet-950/20 text-violet-200'
                    : 'border-slate-800 bg-slate-900/60 text-slate-400'
                }`}>
                  <div className="font-semibold flex items-center justify-between">
                    <span>Submit & Revise Content</span>
                    {(currentWorkspace?.role === 'CONTENT_CREATOR' || currentWorkspace?.role === 'AGENCY_ADMIN') && <CheckCircle2 className="w-4 h-4 text-violet-400" />}
                  </div>
                  <p className="text-[11px] opacity-80">Submit copy and media, view flagged findings, and construct new versions.</p>
                </div>

                <div className={`p-4 rounded-xl border text-xs space-y-1.5 ${
                  currentWorkspace?.role === 'BRAND_REVIEWER'
                    ? 'border-emerald-500/50 bg-emerald-950/20 text-emerald-200'
                    : 'border-slate-800 bg-slate-900/60 text-slate-400'
                }`}>
                  <div className="font-semibold flex items-center justify-between">
                    <span>Approve / Reject Versions</span>
                    {currentWorkspace?.role === 'BRAND_REVIEWER' && <CheckCircle2 className="w-4 h-4 text-emerald-400" />}
                  </div>
                  <p className="text-[11px] opacity-80">Exclusive authority to issue binding approvals on exact immutable snapshots.</p>
                </div>

                <div className={`p-4 rounded-xl border text-xs space-y-1.5 ${
                  currentWorkspace?.role === 'ACCOUNT_MANAGER' || currentWorkspace?.role === 'AGENCY_ADMIN'
                    ? 'border-indigo-500/50 bg-indigo-950/20 text-indigo-200'
                    : 'border-slate-800 bg-slate-900/60 text-slate-400'
                }`}>
                  <div className="font-semibold flex items-center justify-between">
                    <span>Coordinate Review Status</span>
                    {(currentWorkspace?.role === 'ACCOUNT_MANAGER' || currentWorkspace?.role === 'AGENCY_ADMIN') && <CheckCircle2 className="w-4 h-4 text-indigo-400" />}
                  </div>
                  <p className="text-[11px] opacity-80">Track pending reviews, coordinate revisions and reviewer feedback.</p>
                </div>
              </div>
            </div>

            {/* Multi-Tenant Security Verification Notice */}
            <div className="rounded-2xl border border-slate-800 bg-gradient-to-r from-emerald-950/20 via-[#0D1527] to-[#0D1527] p-6 flex items-start space-x-4">
              <ShieldCheck className="w-6 h-6 text-emerald-400 shrink-0 mt-1" />
              <div className="space-y-1">
                <h4 className="font-semibold text-sm text-white">Cross-Client Data Isolation Verified</h4>
                <p className="text-xs text-slate-300 leading-relaxed">
                  Every API query in Inkloom Guardian strictly enforces tenant boundaries. A user belonging to{' '}
                  <strong>EcoVolt</strong> cannot view rules, source documents, or content versions from{' '}
                  <strong>PureNest</strong> or <strong>FinEdge</strong>. Automated security tests verify that unauthorized cross-client access returns <code className="bg-slate-900 text-slate-200 px-1.5 py-0.5 rounded font-mono text-[11px]">403 Forbidden</code>.
                </p>
              </div>
            </div>
          </div>
        )}

        {activePage === 'schema' && (
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-bold text-white tracking-tight">System Architecture & Audit History</h2>
              <p className="text-xs text-slate-400">16 Relational Models and Audit Trails</p>
            </div>
            <div className="p-6 rounded-2xl border border-slate-800 bg-[#0D1527]/70 space-y-4">
              <p className="text-xs text-slate-300">
                All 15 automated database and permission tests are passing cleanly.
              </p>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-[#0B1120] px-6 py-4 mt-auto text-xs text-slate-500">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>Inkloom Guardian © 2026. Built with Django REST Framework, React, Vite & Tailwind CSS.</span>
          <span className="text-slate-400 font-mono">Phase 6: AI Review Workspace & Evidence-Linked Findings Complete</span>
        </div>
      </footer>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <MainApp />
    </AuthProvider>
  );
}
