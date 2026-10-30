import React, { useState } from 'react';
import { ShieldCheck, ChevronDown, LogOut, Briefcase, Check } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Navbar({ activePage, setActivePage }) {
  const { user, memberships, currentWorkspace, selectWorkspace, logout } = useAuth();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const canSubmitContent = ['CONTENT_CREATOR', 'AGENCY_ADMIN'].includes(currentWorkspace?.role);

  const roleBadgeColors = {
    'AGENCY_ADMIN': 'bg-cyan-950/80 text-cyan-300 border-cyan-800/60',
    'BRAND_REVIEWER': 'bg-emerald-950/80 text-emerald-300 border-emerald-800/60',
    'CONTENT_CREATOR': 'bg-violet-950/80 text-violet-300 border-violet-800/60',
    'ACCOUNT_MANAGER': 'bg-indigo-950/80 text-indigo-300 border-indigo-800/60',
  };

  return (
    <header className="border-b border-slate-800/80 bg-[#0B1120]/90 backdrop-blur-md sticky top-0 z-50 px-6 py-3.5">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        {/* Logo & Product Title */}
        <div className="flex items-center space-x-6">
          <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setActivePage('dashboard')}>
            <div className="h-9 w-9 rounded-xl bg-gradient-to-tr from-violet-600 to-cyan-500 p-0.5 shadow-lg shadow-violet-500/20">
              <div className="h-full w-full bg-[#070B14] rounded-[10px] flex items-center justify-center">
                <ShieldCheck className="w-5 h-5 text-cyan-400" />
              </div>
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-base tracking-tight text-white">Inkloom Guardian</span>
                <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-950 text-emerald-300 border border-emerald-800/50">
                  Protected
                </span>
              </div>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center space-x-1 text-xs font-medium">
            <button
              onClick={() => setActivePage('dashboard')}
              className={`px-3 py-1.5 rounded-lg transition cursor-pointer ${
                activePage === 'dashboard'
                  ? 'bg-slate-800 text-white'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
              }`}
            >
              Dashboard
            </button>
            <button
              onClick={() => setActivePage('workspaces')}
              className={`px-3 py-1.5 rounded-lg transition cursor-pointer ${
                activePage === 'workspaces'
                  ? 'bg-slate-800 text-white'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
              }`}
            >
              Client Workspaces
            </button>
            <button
              onClick={() => setActivePage('knowledge')}
              className={`px-3 py-1.5 rounded-lg transition cursor-pointer ${
                activePage === 'knowledge'
                  ? 'bg-slate-800 text-white'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
              }`}
            >
              Brand Knowledge
            </button>
            {canSubmitContent && (
              <button
                onClick={() => setActivePage('submit')}
                className={`px-3 py-1.5 rounded-lg transition cursor-pointer ${
                  activePage === 'submit'
                    ? 'bg-slate-800 text-white'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
                }`}
              >
                Submit Content
              </button>
            )}
            <button
              onClick={() => setActivePage('versions')}
              className={`px-3 py-1.5 rounded-lg transition cursor-pointer ${
                activePage === 'versions'
                  ? 'bg-slate-800 text-white'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
              }`}
            >
              Version History
            </button>
            <button
              onClick={() => setActivePage('review')}
              className={`px-3 py-1.5 rounded-lg transition cursor-pointer ${
                activePage === 'review'
                  ? 'bg-slate-800 text-white'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
              }`}
            >
              ⚖️ Review
            </button>
            <button
              onClick={() => setActivePage('schema')}
              className={`px-3 py-1.5 rounded-lg transition cursor-pointer ${
                activePage === 'schema'
                  ? 'bg-slate-800 text-white'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
              }`}
            >
              Schema & Audit
            </button>
          </nav>
        </div>

        {/* Right Section: Workspace Switcher & User Pill */}
        <div className="flex items-center space-x-3">
          {/* Workspace Switcher Dropdown */}
          <div className="relative">
            <button
              onClick={() => setDropdownOpen(!dropdownOpen)}
              className="flex items-center space-x-2 px-3 py-1.5 rounded-xl border border-slate-700/80 bg-[#0D1527] hover:bg-[#131E36] transition cursor-pointer text-xs"
            >
              <Briefcase className="w-3.5 h-3.5 text-cyan-400" />
              <span className="font-medium text-white max-w-[140px] truncate">
                {currentWorkspace ? currentWorkspace.workspace_name : 'Select Workspace'}
              </span>
              <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
            </button>

            {dropdownOpen && (
              <div className="absolute right-0 mt-2 w-64 rounded-xl border border-slate-800 bg-[#0D1527] shadow-2xl p-2 space-y-1 z-50">
                <div className="px-2.5 py-1.5 text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                  Switch Active Workspace
                </div>
                {memberships.map((m) => (
                  <button
                    key={m.id}
                    onClick={() => {
                      selectWorkspace(m);
                      setDropdownOpen(false);
                    }}
                    className={`w-full text-left px-3 py-2 rounded-lg text-xs flex items-center justify-between transition cursor-pointer ${
                      currentWorkspace && currentWorkspace.id === m.id
                        ? 'bg-violet-950/40 text-violet-200 border border-violet-800/50'
                        : 'text-slate-300 hover:bg-slate-800/70'
                    }`}
                  >
                    <div>
                      <div className="font-medium text-white">{m.workspace_name}</div>
                      <div className="text-[10px] text-slate-400">{m.role_display}</div>
                    </div>
                    {currentWorkspace && currentWorkspace.id === m.id && (
                      <Check className="w-4 h-4 text-violet-400" />
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Role Badge in Current Workspace */}
          {currentWorkspace && (
            <span className={`hidden sm:inline-flex text-[11px] font-semibold px-2.5 py-1 rounded-full border ${roleBadgeColors[currentWorkspace.role] || 'bg-slate-800 text-slate-300'}`}>
              {currentWorkspace.role_display}
            </span>
          )}

          {/* User Profile & Logout */}
          <div className="flex items-center space-x-2 pl-2 border-l border-slate-800">
            <div className="hidden lg:block text-right">
              <div className="text-xs font-medium text-white">{user?.full_name || user?.username}</div>
              <div className="text-[10px] text-slate-400">@{user?.username}</div>
            </div>

            <button
              onClick={logout}
              title="Sign Out"
              className="p-2 rounded-lg text-slate-400 hover:text-red-400 hover:bg-red-950/20 border border-transparent hover:border-red-900/40 transition cursor-pointer"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
