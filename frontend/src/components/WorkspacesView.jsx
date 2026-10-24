import React, { useState, useEffect } from 'react';
import { Briefcase, Users, FileText, CheckCircle2, ShieldCheck, Plus, AlertCircle, Sparkles } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function WorkspacesView() {
  const { token, currentWorkspace, selectWorkspace } = useAuth();
  const [workspaces, setWorkspaces] = useState([]);
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [membersLoading, setMembersLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchWorkspaces();
  }, [token]);

  useEffect(() => {
    if (currentWorkspace?.workspace_id) {
      fetchMembers(currentWorkspace.workspace_id);
    }
  }, [currentWorkspace, token]);

  const fetchWorkspaces = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/workspaces/', {
        headers: { 'Authorization': `Token ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setWorkspaces(data.results || data);
      }
    } catch (err) {
      setError('Failed to fetch workspaces.');
    } finally {
      setLoading(false);
    }
  };

  const fetchMembers = async (wsId) => {
    setMembersLoading(true);
    try {
      const res = await fetch(`/api/workspaces/${wsId}/members/`, {
        headers: { 'Authorization': `Token ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setMembers(data);
      }
    } catch (err) {
      console.error('Error fetching members:', err);
    } finally {
      setMembersLoading(false);
    }
  };

  const roleColors = {
    'AGENCY_ADMIN': 'text-cyan-400 bg-cyan-950/60 border-cyan-800/50',
    'BRAND_REVIEWER': 'text-emerald-400 bg-emerald-950/60 border-emerald-800/50',
    'CONTENT_CREATOR': 'text-violet-400 bg-violet-950/60 border-violet-800/50',
    'ACCOUNT_MANAGER': 'text-indigo-400 bg-indigo-950/60 border-indigo-800/50',
  };

  return (
    <div className="space-y-8">
      {/* Page Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">Client Workspaces (Page 3)</h2>
          <p className="text-xs text-slate-400">
            Isolated brand governance environments. Every rule, claim, and source document is strictly scoped.
          </p>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-950/30 border border-red-800/50 text-red-300 text-xs flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 text-red-400" />
          <span>{error}</span>
        </div>
      )}

      {/* Accessible Workspaces Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {workspaces.map((ws) => {
          const isSelected = currentWorkspace?.workspace_id === ws.id;
          return (
            <div
              key={ws.id}
              className={`rounded-2xl border p-6 transition flex flex-col justify-between ${
                isSelected
                  ? 'border-cyan-500/80 bg-gradient-to-b from-[#0D1527] to-[#111A30] shadow-xl shadow-cyan-500/10'
                  : 'border-slate-800 bg-[#0D1527]/70 hover:border-slate-700'
              }`}
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-800">
                    /{ws.slug}
                  </span>
                  {isSelected && (
                    <span className="inline-flex items-center space-x-1 text-[10px] font-semibold text-cyan-300 bg-cyan-950 px-2 py-0.5 rounded-full border border-cyan-800/50">
                      <CheckCircle2 className="w-3 h-3 text-cyan-400" />
                      <span>Active Workspace</span>
                    </span>
                  )}
                </div>

                <div>
                  <h3 className="text-lg font-bold text-white">{ws.name}</h3>
                  <p className="text-xs text-slate-400 mt-0.5">{ws.industry || 'Multi-channel'}</p>
                </div>

                <p className="text-xs text-slate-300 line-clamp-2">
                  {ws.description || 'Dedicated client workspace with strict data isolation.'}
                </p>

                {/* Workspace Counts */}
                <div className="grid grid-cols-3 gap-2 pt-2 border-t border-slate-800/80 text-center">
                  <div className="p-2 rounded bg-slate-900/60 border border-slate-800">
                    <div className="text-sm font-bold text-white">{ws.rules_count ?? 0}</div>
                    <div className="text-[10px] text-slate-500">Rules</div>
                  </div>
                  <div className="p-2 rounded bg-slate-900/60 border border-slate-800">
                    <div className="text-sm font-bold text-emerald-400">{ws.claims_count ?? 0}</div>
                    <div className="text-[10px] text-slate-500">Claims</div>
                  </div>
                  <div className="p-2 rounded bg-slate-900/60 border border-slate-800">
                    <div className="text-sm font-bold text-indigo-400">{ws.sources_count ?? 0}</div>
                    <div className="text-[10px] text-slate-500">Sources</div>
                  </div>
                </div>
              </div>

              <div className="pt-4 mt-4 border-t border-slate-800/80">
                <button
                  onClick={() => selectWorkspace({ workspace_id: ws.id, workspace_name: ws.name, workspace_slug: ws.slug })}
                  className={`w-full py-2 px-3 rounded-xl text-xs font-medium transition cursor-pointer ${
                    isSelected
                      ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                      : 'bg-slate-900 text-slate-300 hover:bg-slate-800 border border-slate-700'
                  }`}
                >
                  {isSelected ? 'Currently Selected' : 'Switch To This Workspace'}
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Selected Workspace Members Directory */}
      <div className="rounded-2xl border border-slate-800 bg-[#0D1527]/70 p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Users className="w-5 h-5 text-cyan-400" />
            <h3 className="font-semibold text-white">
              {currentWorkspace ? `${currentWorkspace.workspace_name} — Member Roles` : 'Workspace Members'}
            </h3>
          </div>
          <span className="text-xs text-slate-400">
            Backend Enforced RBAC (Role-Based Access Control)
          </span>
        </div>

        {membersLoading ? (
          <div className="text-xs text-slate-400 py-4">Loading assigned workspace members...</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-900/80 uppercase text-[10px] font-semibold tracking-wider text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="px-4 py-3">Member</th>
                  <th className="px-4 py-3">Username / Email</th>
                  <th className="px-4 py-3">Assigned Role</th>
                  <th className="px-4 py-3">Role Authority</th>
                  <th className="px-4 py-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-normal">
                {members.map((m) => (
                  <tr key={m.id} className="hover:bg-slate-800/30 transition">
                    <td className="px-4 py-3 font-medium text-white">
                      {m.user.full_name}
                    </td>
                    <td className="px-4 py-3 text-slate-400 font-mono">
                      @{m.user.username} <span className="text-slate-600">({m.user.email})</span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-semibold border ${roleColors[m.role] || 'bg-slate-800 text-slate-300'}`}>
                        {m.role_display}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-400 text-[11px]">
                      {m.role === 'AGENCY_ADMIN' && 'Configure brand rules, claims, and invite members.'}
                      {m.role === 'BRAND_REVIEWER' && 'Exclusive authority to approve/reject immutable versions.'}
                      {m.role === 'CONTENT_CREATOR' && 'Submit copy & images, accept suggestions, spawn revisions.'}
                      {m.role === 'ACCOUNT_MANAGER' && 'Track reviews, coordinate comments and deliverables.'}
                    </td>
                    <td className="px-4 py-3">
                      <span className="inline-flex items-center space-x-1 text-emerald-400">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                        <span className="text-[11px]">Active</span>
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
