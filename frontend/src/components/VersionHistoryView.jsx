import apiFetch from "../api";
import React, { useState, useEffect, useCallback } from 'react';
import { 
  GitBranch, 
  CheckCircle2, 
  AlertCircle, 
  Lock, 
  Plus, 
  X,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function VersionHistoryView() {
  const { token, currentWorkspace } = useAuth();
  const canCreateRevision = ['CONTENT_CREATOR', 'AGENCY_ADMIN'].includes(currentWorkspace?.role);
  const [contentItems, setContentItems] = useState([]);
  const [selectedItem, setSelectedItem] = useState(null);
  const [itemDetail, setItemDetail] = useState(null);
  const [loading, setLoading] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState(null);

  // Revision Modal State
  const [showRevisionModal, setShowRevisionModal] = useState(false);
  const [revisedText, setRevisedText] = useState('');
  const [revisionLoading, setRevisionLoading] = useState(false);

  const fetchItemDetail = useCallback(async (itemId) => {
    setDetailLoading(true);
    try {
      const res = await apiFetch(`/api/content/${itemId}/`, {
        headers: { 'Authorization': `Token ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setItemDetail(data);
        setSelectedItem(data);
      }
    } catch (err) {
      console.error('Error fetching content detail:', err);
    } finally {
      setDetailLoading(false);
    }
  }, [token]);

  const fetchWorkspaceContent = useCallback(async () => {
    if (!currentWorkspace?.workspace_id) return;
    setLoading(true);
    setError(null);
    try {
      const res = await apiFetch(`/api/workspaces/${currentWorkspace.workspace_id}/content/`, {
        headers: { 'Authorization': `Token ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setContentItems(data);
        if (data.length > 0 && !selectedItem) {
          await fetchItemDetail(data[0].id);
        }
      }
    } catch {
      setError('Failed to fetch workspace content.');
    } finally {
      setLoading(false);
    }
  }, [currentWorkspace, fetchItemDetail, selectedItem, token]);

  useEffect(() => {
    if (currentWorkspace?.workspace_id) {
      fetchWorkspaceContent();
    }
  }, [currentWorkspace, fetchWorkspaceContent]);

  const handleOpenRevision = () => {
    if (itemDetail && itemDetail.versions && itemDetail.versions.length > 0) {
      setRevisedText(itemDetail.versions[0].raw_text);
    }
    setShowRevisionModal(true);
  };

  const handleSubmitRevision = async (e) => {
    e.preventDefault();
    if (!itemDetail) return;
    setRevisionLoading(true);
    try {
      const res = await apiFetch(`/api/content/${itemDetail.id}/versions/`, {
        method: 'POST',
        headers: {
          'Authorization': `Token ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ raw_text: revisedText })
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Failed to spawn revision.');
      }

      setShowRevisionModal(false);
      // Refresh current item's version tree
      fetchItemDetail(itemDetail.id);
      fetchWorkspaceContent();
    } catch (err) {
      alert(`Error creating revision: ${err.message}`);
    } finally {
      setRevisionLoading(false);
    }
  };

  const statusColors = {
    'APPROVED': 'bg-emerald-950/80 text-emerald-300 border-emerald-800/60',
    'SUBMITTED': 'bg-cyan-950/80 text-cyan-300 border-cyan-800/60',
    'PROCESSING': 'bg-violet-950/80 text-violet-300 border-violet-800/60',
    'NEEDS_CHANGES': 'bg-amber-950/80 text-amber-300 border-amber-800/60',
    'REJECTED': 'bg-red-950/80 text-red-300 border-red-800/60',
    'DRAFT': 'bg-slate-800 text-slate-300 border-slate-700',
  };

  return (
    <div className="space-y-8">
      {/* Title */}
      <div>
        <div className="flex items-center space-x-2">
          <h2 className="text-2xl font-bold text-white tracking-tight">Version History & Lineage (Page 9)</h2>
          <span className="text-xs px-2.5 py-0.5 rounded-full bg-cyan-950 text-cyan-300 border border-cyan-800/50">
            {currentWorkspace ? currentWorkspace.workspace_name : 'No Workspace'}
          </span>
        </div>
        <p className="text-xs text-slate-400 mt-1">
          Cryptographically immutable version snapshots. A revision never inherits approval from an earlier version.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-950/30 border border-red-800/50 text-red-300 text-xs flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 text-red-400" />
          <span>{error}</span>
        </div>
      )}

      {/* Main Grid: Left Item Selector, Right Version Lineage */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Content Items List */}
        <div className="space-y-3">
          <div className="flex items-center justify-between text-xs font-semibold uppercase tracking-wider text-slate-400">
            <span>Submitted Content Items ({contentItems.length})</span>
          </div>

          {loading ? (
            <div className="text-xs text-slate-400 p-4">Loading content items...</div>
          ) : contentItems.length === 0 ? (
            <div className="p-6 rounded-2xl border border-slate-800 bg-[#0D1527]/50 text-center text-xs text-slate-400">
              No content items submitted yet for this workspace. Use the Content Submission tab to create one.
            </div>
          ) : (
            <div className="space-y-2">
              {contentItems.map((item) => {
                const isSelected = selectedItem?.id === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => fetchItemDetail(item.id)}
                    className={`w-full text-left p-4 rounded-xl border transition cursor-pointer ${
                      isSelected
                        ? 'border-violet-500/80 bg-violet-950/20 shadow-lg shadow-violet-500/10'
                        : 'border-slate-800 bg-[#0D1527]/80 hover:border-slate-700'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-sm text-white truncate max-w-[200px]">
                        {item.title}
                      </span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-900 text-cyan-300 border border-slate-800">
                        {item.versions_count} ver(s)
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 mt-1 line-clamp-1">{item.description || 'No description provided.'}</p>
                    <div className="text-[10px] text-slate-500 mt-2 font-mono">
                      By @{item.created_by?.username} â€¢ {new Date(item.created_at).toLocaleDateString()}
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Right Column: Version Lineage Details */}
        <div className="lg:col-span-2 space-y-4">
          {detailLoading ? (
            <div className="p-8 rounded-2xl border border-slate-800 bg-[#0D1527]/80 text-center text-xs text-slate-400">
              Loading immutable version history...
            </div>
          ) : itemDetail ? (
            <div className="rounded-2xl border border-slate-800 bg-[#0D1527]/80 p-6 md:p-8 space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
                <div>
                  <h3 className="text-xl font-bold text-white">{itemDetail.title}</h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Total Revisions: {itemDetail.versions?.length} â€¢ Workspace: {currentWorkspace?.workspace_name}
                  </p>
                </div>

                {canCreateRevision && (
                  <button
                    onClick={handleOpenRevision}
                    className="px-4 py-2 rounded-xl bg-violet-600 hover:bg-violet-500 text-white font-medium text-xs flex items-center space-x-1.5 shadow-lg shadow-violet-600/25 transition cursor-pointer"
                  >
                    <Plus className="w-4 h-4" />
                    <span>Spawn Revision (v{(itemDetail.versions?.[0]?.version_number || 1) + 1})</span>
                  </button>
                )}
              </div>

              {/* Version Snapshots Tree */}
              <div className="space-y-4">
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center space-x-1.5">
                  <GitBranch className="w-4 h-4 text-violet-400" />
                  <span>Immutable Version Lineage</span>
                </span>

                {itemDetail.versions && itemDetail.versions.map((ver, idx) => (
                  <div
                    key={ver.id}
                    className={`p-5 rounded-xl border space-y-3.5 transition ${
                      idx === 0
                        ? 'border-violet-500/60 bg-slate-900/90 shadow-md'
                        : 'border-slate-800 bg-slate-900/50'
                    }`}
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center space-x-2.5">
                        <span className="text-xs font-bold font-mono px-2.5 py-1 rounded-lg bg-violet-950 text-violet-300 border border-violet-800/60">
                          v{ver.version_number}
                        </span>
                        {idx === 0 && (
                          <span className="text-[10px] font-semibold text-cyan-300 bg-cyan-950 px-2 py-0.5 rounded-full border border-cyan-800/40">
                            Latest Version
                          </span>
                        )}
                        <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${statusColors[ver.status] || 'bg-slate-800 text-slate-300'}`}>
                          {ver.status_display}
                        </span>
                        {ver.has_approval && (
                          <span className="text-[10px] font-bold text-emerald-400 bg-emerald-950/70 px-2 py-0.5 rounded border border-emerald-800/50 flex items-center space-x-1">
                            <CheckCircle2 className="w-3 h-3" />
                            <span>Approved Snapshot</span>
                          </span>
                        )}
                      </div>

                      <div className="text-[11px] text-slate-500 font-mono">
                        {new Date(ver.created_at).toLocaleString()}
                      </div>
                    </div>

                    {/* Copy text */}
                    <div className="bg-slate-950/70 p-3.5 rounded-lg border border-slate-800/80 text-xs text-slate-200 leading-relaxed font-sans">
                      {ver.raw_text}
                    </div>

                    {/* Cryptographic SHA-256 Hash */}
                    <div className="flex items-center space-x-2 text-[10px] text-slate-500 font-mono bg-slate-950/40 px-2.5 py-1 rounded border border-slate-800/60">
                      <Lock className="w-3 h-3 text-cyan-400 shrink-0" />
                      <span className="text-slate-400">SHA-256:</span>
                      <span className="text-slate-300 truncate">{ver.checksum_sha256}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="p-8 rounded-2xl border border-slate-800 bg-[#0D1527]/50 text-center text-xs text-slate-400">
              Select a content item from the left to view its immutable version history.
            </div>
          )}
        </div>
      </div>

      {/* SPAWN REVISION MODAL */}
      {showRevisionModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-xl rounded-2xl border border-slate-800 bg-[#0D1527] p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h3 className="font-bold text-white text-base">Spawn New Content Revision</h3>
                <p className="text-[11px] text-slate-400">Creates v{(itemDetail?.versions?.[0]?.version_number || 1) + 1} with a fresh SHA-256 hash.</p>
              </div>
              <button onClick={() => setShowRevisionModal(false)} className="text-slate-400 hover:text-white cursor-pointer">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-3 rounded-xl bg-amber-950/30 border border-amber-800/50 text-[11px] text-amber-300 space-y-1">
              <strong>Compliance Notice:</strong>
              <p>This revision will reset governance status to <strong>SUBMITTED</strong>. It will NOT inherit approval from earlier versions.</p>
            </div>

            <form onSubmit={handleSubmitRevision} className="space-y-4 text-xs">
              <div className="space-y-1.5">
                <label className="text-slate-300 font-medium">Edit Marketing Copy</label>
                <textarea
                  required
                  rows="6"
                  value={revisedText}
                  onChange={(e) => setRevisedText(e.target.value)}
                  className="w-full p-3.5 rounded-xl bg-slate-900 border border-slate-700 text-white text-xs leading-relaxed focus:outline-none focus:border-violet-500"
                />
              </div>

              <div className="pt-2 flex justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setShowRevisionModal(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 hover:bg-slate-700 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={revisionLoading || !revisedText.trim()}
                  className="px-4 py-2 rounded-xl bg-violet-600 hover:bg-violet-500 text-white font-medium cursor-pointer disabled:opacity-50"
                >
                  {revisionLoading ? 'Creating v...' : 'Save & Submit Revision'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
