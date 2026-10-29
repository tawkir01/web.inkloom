import apiFetch from "../api";
import React, { useState, useEffect } from 'react';
import { 
  BookOpen, 
  Scale, 
  FileCheck2, 
  Plus, 
  CheckCircle2, 
  AlertCircle, 
  Filter, 
  Search, 
  Calendar, 
  ShieldAlert, 
  ExternalLink,
  ChevronRight,
  Info,
  X
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function BrandKnowledgeView() {
  const { token, currentWorkspace } = useAuth();
  const [activeTab, setActiveTab] = useState('rules');
  const [rules, setRules] = useState([]);
  const [claims, setClaims] = useState([]);
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Filters
  const [ruleTypeFilter, setRuleTypeFilter] = useState('');
  const [severityFilter, setSeverityFilter] = useState('');

  // Modals
  const [showRuleModal, setShowRuleModal] = useState(false);
  const [showClaimModal, setShowClaimModal] = useState(false);
  const [showSourceModal, setShowSourceModal] = useState(false);
  const [sourceVersionModal, setSourceVersionModal] = useState(null);
  const [savingSourceVersion, setSavingSourceVersion] = useState(false);

  // New Rule Form State
  const [newRule, setNewRule] = useState({
    name: '',
    rule_type: 'PROHIBITED_PHRASE',
    pattern_or_phrase: '',
    preferred_alternative: '',
    explanation: '',
    severity: 'HIGH',
    is_active: true
  });

  // New Claim Form State
  const [newClaim, setNewClaim] = useState({
    claim_title: '',
    permitted_statement: '',
    required_qualifiers: '',
    disallowed_variations: '',
    source_version: '',
    category: 'General',
    is_active: true
  });

  // New Source Form State
  const [newSource, setNewSource] = useState({
    document_code: '',
    title: '',
    description: ''
  });

  const [newSourceVersion, setNewSourceVersion] = useState({
    version_label: 'v1.0',
    full_text_content: '',
    passage_texts: '',
    effective_date: '',
    expiration_date: '',
    is_approved: true
  });

  const canEdit = currentWorkspace?.role === 'AGENCY_ADMIN';

  useEffect(() => {
    if (currentWorkspace?.workspace_id) {
      fetchKnowledgeData();
    }
  }, [currentWorkspace, token]);

  const fetchKnowledgeData = async () => {
    if (!currentWorkspace?.workspace_id) return;
    setLoading(true);
    setError(null);
    const wsId = currentWorkspace.workspace_id;

    try {
      const headers = { 'Authorization': `Token ${token}` };
      const [rulesRes, claimsRes, sourcesRes] = await Promise.all([
        apiFetch(`/api/workspaces/${wsId}/rules/`, { headers }),
        apiFetch(`/api/workspaces/${wsId}/claims/`, { headers }),
        apiFetch(`/api/workspaces/${wsId}/sources/`, { headers }),
      ]);

      if (rulesRes.ok) {
        const data = await rulesRes.json();
        setRules(data.results || data);
      }
      if (claimsRes.ok) {
        const data = await claimsRes.json();
        setClaims(data.results || data);
      }
      if (sourcesRes.ok) {
        const data = await sourcesRes.json();
        setSources(data.results || data);
      }
    } catch (err) {
      setError('Failed to fetch brand knowledge records.');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateRule = async (e) => {
    e.preventDefault();
    try {
      const res = await apiFetch(`/api/workspaces/${currentWorkspace.workspace_id}/rules/`, {
        method: 'POST',
        headers: {
          'Authorization': `Token ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(newRule)
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(JSON.stringify(data));
      }
      setShowRuleModal(false);
      setNewRule({
        name: '',
        rule_type: 'PROHIBITED_PHRASE',
        pattern_or_phrase: '',
        preferred_alternative: '',
        explanation: '',
        severity: 'HIGH',
        is_active: true
      });
      fetchKnowledgeData();
    } catch (err) {
      alert(`Error creating rule: ${err.message}`);
    }
  };

  const handleCreateClaim = async (e) => {
    e.preventDefault();
    try {
      const res = await apiFetch(`/api/workspaces/${currentWorkspace.workspace_id}/claims/`, {
        method: 'POST',
        headers: {
          'Authorization': `Token ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          ...newClaim,
          source_version: newClaim.source_version || null
        })
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(JSON.stringify(data));
      }
      setShowClaimModal(false);
      setNewClaim({
        claim_title: '',
        permitted_statement: '',
        required_qualifiers: '',
        disallowed_variations: '',
        source_version: '',
        category: 'General',
        is_active: true
      });
      fetchKnowledgeData();
    } catch (err) {
      alert(`Error creating claim: ${err.message}`);
    }
  };

  const handleCreateSource = async (e) => {
    e.preventDefault();
    try {
      const res = await apiFetch(`/api/workspaces/${currentWorkspace.workspace_id}/sources/`, {
        method: 'POST',
        headers: {
          'Authorization': `Token ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(newSource)
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(JSON.stringify(data));
      }
      setShowSourceModal(false);
      setNewSource({ document_code: '', title: '', description: '' });
      fetchKnowledgeData();
    } catch (err) {
      alert(`Error registering source: ${err.message}`);
    }
  };

  const handleCreateSourceVersion = async (e) => {
    e.preventDefault();
    if (!sourceVersionModal) return;

    setSavingSourceVersion(true);
    try {
      const res = await apiFetch(`/api/sources/${sourceVersionModal.id}/versions/`, {
        method: 'POST',
        headers: {
          'Authorization': `Token ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          version_label: newSourceVersion.version_label,
          full_text_content: newSourceVersion.full_text_content,
          passage_excerpts: newSourceVersion.passage_texts
            .split('\n')
            .map((text) => text.trim())
            .filter(Boolean)
            .map((text, index) => ({ passage_id: `P${index + 1}`, text })),
          effective_date: newSourceVersion.effective_date || null,
          expiration_date: newSourceVersion.expiration_date || null,
          is_approved: newSourceVersion.is_approved
        })
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(JSON.stringify(data));
      }

      setSourceVersionModal(null);
      setNewSourceVersion({
        version_label: 'v1.0',
        full_text_content: '',
        passage_texts: '',
        effective_date: '',
        expiration_date: '',
        is_approved: true
      });
      await fetchKnowledgeData();
    } catch (err) {
      alert(`Error adding source version: ${err.message}`);
    } finally {
      setSavingSourceVersion(false);
    }
  };

  const severityBadges = {
    'CRITICAL': 'bg-red-950/80 text-red-300 border-red-800/60',
    'HIGH': 'bg-amber-950/80 text-amber-300 border-amber-800/60',
    'MEDIUM': 'bg-indigo-950/80 text-indigo-300 border-indigo-800/60',
    'LOW': 'bg-slate-800 text-slate-300 border-slate-700',
  };

  const filteredRules = rules.filter(r => {
    if (ruleTypeFilter && r.rule_type !== ruleTypeFilter) return false;
    if (severityFilter && r.severity !== severityFilter) return false;
    return true;
  });

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <h2 className="text-2xl font-bold text-white tracking-tight">Brand Knowledge Management (Page 4)</h2>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-cyan-950 text-cyan-300 border border-cyan-800/50">
              {currentWorkspace ? currentWorkspace.workspace_name : 'No Workspace'}
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Deterministic brand rules, approved claims, and versioned evidentiary source benchmarks.
          </p>
        </div>

        {/* Action Button based on Role */}
        <div>
          {canEdit ? (
            <div className="flex items-center space-x-2">
              {activeTab === 'rules' && (
                <button
                  onClick={() => setShowRuleModal(true)}
                  className="px-3.5 py-2 rounded-xl bg-violet-600 hover:bg-violet-500 text-white font-medium text-xs flex items-center space-x-1.5 shadow-lg shadow-violet-600/25 transition cursor-pointer"
                >
                  <Plus className="w-4 h-4" />
                  <span>New Brand Rule</span>
                </button>
              )}
              {activeTab === 'claims' && (
                <button
                  onClick={() => setShowClaimModal(true)}
                  className="px-3.5 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-medium text-xs flex items-center space-x-1.5 shadow-lg shadow-cyan-600/25 transition cursor-pointer"
                >
                  <Plus className="w-4 h-4" />
                  <span>Register Claim</span>
                </button>
              )}
              {activeTab === 'sources' && (
                <button
                  onClick={() => setShowSourceModal(true)}
                  className="px-3.5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-xs flex items-center space-x-1.5 shadow-lg shadow-emerald-600/25 transition cursor-pointer"
                >
                  <Plus className="w-4 h-4" />
                  <span>Register Source</span>
                </button>
              )}
            </div>
          ) : (
            <div className="inline-flex items-center space-x-1.5 text-xs text-slate-400 bg-slate-900 px-3 py-1.5 rounded-lg border border-slate-800">
              <Info className="w-3.5 h-3.5 text-amber-400" />
              <span>Agency Admin role required to create or alter brand records.</span>
            </div>
          )}
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-950/30 border border-red-800/50 text-red-300 text-xs flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 text-red-400" />
          <span>{error}</span>
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-slate-800 flex space-x-6 text-sm">
        <button
          onClick={() => setActiveTab('rules')}
          className={`pb-3 font-medium transition cursor-pointer flex items-center space-x-2 border-b-2 ${
            activeTab === 'rules'
              ? 'border-violet-500 text-violet-300'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Scale className="w-4 h-4" />
          <span>Brand Rules ({rules.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('claims')}
          className={`pb-3 font-medium transition cursor-pointer flex items-center space-x-2 border-b-2 ${
            activeTab === 'claims'
              ? 'border-cyan-500 text-cyan-300'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <FileCheck2 className="w-4 h-4" />
          <span>Approved Claims ({claims.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('sources')}
          className={`pb-3 font-medium transition cursor-pointer flex items-center space-x-2 border-b-2 ${
            activeTab === 'sources'
              ? 'border-emerald-500 text-emerald-300'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <BookOpen className="w-4 h-4" />
          <span>Source Documents ({sources.length})</span>
        </button>
      </div>

      {/* TAB 1: BRAND RULES */}
      {activeTab === 'rules' && (
        <div className="space-y-4">
          {/* Filters Bar */}
          <div className="flex flex-wrap items-center gap-3 bg-[#0D1527]/70 p-3.5 rounded-xl border border-slate-800 text-xs">
            <span className="text-slate-400 font-medium flex items-center space-x-1">
              <Filter className="w-3.5 h-3.5 text-violet-400" />
              <span>Filters:</span>
            </span>

            <select
              value={ruleTypeFilter}
              onChange={(e) => setRuleTypeFilter(e.target.value)}
              className="bg-slate-900 border border-slate-700/80 rounded-lg px-2.5 py-1 text-slate-200 focus:outline-none focus:border-violet-500"
            >
              <option value="">All Rule Types</option>
              <option value="PROHIBITED_PHRASE">Prohibited Phrase</option>
              <option value="REQUIRED_TERM">Required Term</option>
              <option value="REQUIRED_QUALIFIER">Required Qualifier</option>
              <option value="DISALLOWED_CLAIM">Disallowed Claim</option>
              <option value="TONE_GUIDANCE">Tone Guidance</option>
            </select>

            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="bg-slate-900 border border-slate-700/80 rounded-lg px-2.5 py-1 text-slate-200 focus:outline-none focus:border-violet-500"
            >
              <option value="">All Severities</option>
              <option value="CRITICAL">Critical</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
            </select>

            {(ruleTypeFilter || severityFilter) && (
              <button
                onClick={() => { setRuleTypeFilter(''); setSeverityFilter(''); }}
                className="text-violet-400 hover:text-violet-300 text-xs underline cursor-pointer"
              >
                Reset Filters
              </button>
            )}
          </div>

          {/* Rules List */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredRules.map((rule) => (
              <div
                key={rule.id}
                className="rounded-2xl border border-slate-800 bg-[#0D1527]/80 p-5 space-y-3.5 hover:border-slate-700 transition"
              >
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <h4 className="font-semibold text-white text-sm">{rule.name}</h4>
                    <span className="text-[10px] text-slate-400">{rule.rule_type_display}</span>
                  </div>
                  <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${severityBadges[rule.severity]}`}>
                    {rule.severity_display}
                  </span>
                </div>

                <div className="space-y-2 text-xs">
                  <div className="bg-red-950/30 border border-red-900/40 p-2.5 rounded-lg">
                    <span className="text-[10px] uppercase font-bold text-red-400 block mb-0.5">Flag Pattern / Phrase:</span>
                    <code className="text-red-200 font-mono text-[11px] break-all">{rule.pattern_or_phrase}</code>
                  </div>

                  {rule.preferred_alternative && (
                    <div className="bg-emerald-950/30 border border-emerald-900/40 p-2.5 rounded-lg">
                      <span className="text-[10px] uppercase font-bold text-emerald-400 block mb-0.5">Approved Alternative:</span>
                      <span className="text-emerald-200 text-xs">{rule.preferred_alternative}</span>
                    </div>
                  )}

                  <p className="text-slate-300 text-xs pt-1 leading-relaxed">
                    <strong className="text-slate-400">Policy Reason:</strong> {rule.explanation}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 2: APPROVED CLAIMS */}
      {activeTab === 'claims' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {claims.map((claim) => (
            <div
              key={claim.id}
              className="rounded-2xl border border-slate-800 bg-[#0D1527]/80 p-6 space-y-4 hover:border-slate-700 transition"
            >
              <div className="flex items-center justify-between">
                <h4 className="font-bold text-white text-base">{claim.claim_title}</h4>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800/50">
                  {claim.category}
                </span>
              </div>

              <div className="space-y-3 text-xs">
                <div className="bg-emerald-950/25 border border-emerald-800/40 p-3 rounded-xl space-y-1">
                  <span className="text-[10px] uppercase font-bold text-emerald-400">Exact Permitted Statement:</span>
                  <p className="text-emerald-100 font-medium text-xs leading-relaxed">"{claim.permitted_statement}"</p>
                </div>

                {claim.required_qualifiers && (
                  <div className="bg-amber-950/20 border border-amber-800/40 p-3 rounded-xl space-y-1">
                    <span className="text-[10px] uppercase font-bold text-amber-400">Mandatory Qualifiers & Conditions:</span>
                    <p className="text-amber-200 text-xs">{claim.required_qualifiers}</p>
                  </div>
                )}

                {claim.source_version && (
                  <div className="bg-cyan-950/25 border border-cyan-800/40 p-3 rounded-xl space-y-1">
                    <span className="text-[10px] uppercase font-bold text-cyan-400">Supporting Approved Source:</span>
                    <p className="text-cyan-100 text-xs">
                      {claim.source_document_code} · {claim.source_document_title} [{claim.source_version_label}]
                    </p>
                  </div>
                )}

                {claim.disallowed_variations && (
                  <div className="bg-red-950/20 border border-red-800/40 p-3 rounded-xl space-y-1">
                    <span className="text-[10px] uppercase font-bold text-red-400">Disallowed Exaggerations:</span>
                    <p className="text-red-200 text-xs">{claim.disallowed_variations}</p>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* TAB 3: SOURCE DOCUMENTS & VERSIONS */}
      {activeTab === 'sources' && (
        <div className="space-y-5">
          {sources.map((source) => (
            <div
              key={source.id}
              className="rounded-2xl border border-slate-800 bg-[#0D1527]/80 p-6 space-y-4"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800/80 pb-4">
                <div className="flex items-center space-x-3">
                  <div className="p-2.5 rounded-xl bg-emerald-950/60 border border-emerald-800/50 text-emerald-400">
                    <BookOpen className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="flex items-center space-x-2">
                      <h4 className="font-bold text-white text-base">{source.title}</h4>
                      <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-900 text-emerald-400 border border-slate-800">
                        {source.document_code}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 mt-0.5">{source.description || 'Verified benchmark documentation.'}</p>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <span className="text-xs text-slate-400 font-mono">
                    {source.versions?.length || 0} Registered Version(s)
                  </span>
                  {canEdit && (
                    <button
                      type="button"
                      onClick={() => setSourceVersionModal(source)}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-950/70 border border-emerald-800/60 text-emerald-300 hover:bg-emerald-900/70"
                    >
                      <Plus className="w-3.5 h-3.5" />
                      Add Version
                    </button>
                  )}
                </div>
              </div>

              {/* Version History & Stored Passages */}
              <div className="space-y-3">
                <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                  Versioned Evidence Passages
                </span>

                {source.versions && source.versions.map((ver) => (
                  <div key={ver.id} className="p-4 rounded-xl bg-slate-900/70 border border-slate-800 space-y-3">
                    <div className="flex items-center justify-between text-xs">
                      <div className="flex items-center space-x-2">
                        <span className="font-bold text-white font-mono text-sm">{ver.version_label}</span>
                        {ver.is_currently_valid ? (
                          <span className="text-[10px] font-semibold text-emerald-300 bg-emerald-950 px-2 py-0.5 rounded-full border border-emerald-800/40">
                            Active & Approved
                          </span>
                        ) : (
                          <span className="text-[10px] font-semibold text-red-300 bg-red-950 px-2 py-0.5 rounded-full border border-red-800/40">
                            Expired / Stale
                          </span>
                        )}
                      </div>

                      <div className="text-[11px] text-slate-400 flex items-center space-x-3">
                        {ver.effective_date && <span>Effective: {ver.effective_date}</span>}
                        {ver.expiration_date && <span>Expires: {ver.expiration_date}</span>}
                      </div>
                    </div>

                    <p className="text-xs text-slate-300 leading-relaxed italic bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
                      "{ver.full_text_content}"
                    </p>

                    {ver.passage_excerpts && ver.passage_excerpts.length > 0 && (
                      <div className="space-y-1.5 pt-1">
                        <span className="text-[10px] uppercase font-bold text-slate-400">Indexed Citations:</span>
                        <div className="flex flex-wrap gap-2">
                          {ver.passage_excerpts.map((p, idx) => (
                            <div key={idx} className="text-[11px] px-2.5 py-1 rounded bg-slate-950 text-slate-300 border border-slate-800 flex items-center space-x-1.5">
                              <span className="text-cyan-400 font-mono font-bold">{p.passage_id || `P${idx+1}`}:</span>
                              <span>"{p.text}"</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* CREATE RULE MODAL */}
      {showRuleModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-lg rounded-2xl border border-slate-800 bg-[#0D1527] p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="font-bold text-white text-base">Create New Brand Rule</h3>
              <button onClick={() => setShowRuleModal(false)} className="text-slate-400 hover:text-white cursor-pointer">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateRule} className="space-y-3.5 text-xs">
              <div>
                <label className="text-slate-300 font-medium block mb-1">Rule Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Prohibit Unsubstantiated Guarantees"
                  value={newRule.name}
                  onChange={(e) => setNewRule({ ...newRule, name: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-white"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-slate-300 font-medium block mb-1">Rule Type</label>
                  <select
                    value={newRule.rule_type}
                    onChange={(e) => setNewRule({ ...newRule, rule_type: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-white"
                  >
                    <option value="PROHIBITED_PHRASE">Prohibited Phrase</option>
                    <option value="REQUIRED_TERM">Required Term</option>
                    <option value="REQUIRED_QUALIFIER">Required Qualifier</option>
                    <option value="DISALLOWED_CLAIM">Disallowed Claim</option>
                    <option value="TONE_GUIDANCE">Tone Guidance</option>
                  </select>
                </div>

                <div>
                  <label className="text-slate-300 font-medium block mb-1">Severity</label>
                  <select
                    value={newRule.severity}
                    onChange={(e) => setNewRule({ ...newRule, severity: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-white"
                  >
                    <option value="CRITICAL">Critical</option>
                    <option value="HIGH">High</option>
                    <option value="MEDIUM">Medium</option>
                    <option value="LOW">Low</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="text-slate-300 font-medium block mb-1">Flag Pattern or Exact Phrase</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. guaranteed 50%"
                  value={newRule.pattern_or_phrase}
                  onChange={(e) => setNewRule({ ...newRule, pattern_or_phrase: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-white font-mono text-[11px]"
                />
              </div>

              <div>
                <label className="text-slate-300 font-medium block mb-1">Approved Alternative (Optional)</label>
                <input
                  type="text"
                  placeholder="e.g. save up to 20%"
                  value={newRule.preferred_alternative}
                  onChange={(e) => setNewRule({ ...newRule, preferred_alternative: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-white"
                />
              </div>

              <div>
                <label className="text-slate-300 font-medium block mb-1">Policy Explanation</label>
                <textarea
                  required
                  rows="3"
                  placeholder="Explain why this rule was triggered and what creators must do."
                  value={newRule.explanation}
                  onChange={(e) => setNewRule({ ...newRule, explanation: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-white"
                />
              </div>

              <div className="pt-2 flex justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setShowRuleModal(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 hover:bg-slate-700 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl bg-violet-600 hover:bg-violet-500 text-white font-medium cursor-pointer"
                >
                  Save Brand Rule
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* CREATE CLAIM MODAL */}
      {showClaimModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-lg rounded-2xl border border-slate-800 bg-[#0D1527] p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="font-bold text-white text-base">Register Approved Claim</h3>
              <button onClick={() => setShowClaimModal(false)} className="text-slate-400 hover:text-white cursor-pointer">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateClaim} className="space-y-3.5 text-xs">
              <div>
                <label className="text-slate-300 font-medium block mb-1">Claim Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Annual Energy Efficiency"
                  value={newClaim.claim_title}
                  onChange={(e) => setNewClaim({ ...newClaim, claim_title: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-white"
                />
              </div>

              <div>
                <label className="text-slate-300 font-medium block mb-1">Category</label>
                <input
                  type="text"
                  placeholder="e.g. Efficiency, Safety, Performance"
                  value={newClaim.category}
                  onChange={(e) => setNewClaim({ ...newClaim, category: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-white"
                />
              </div>

              <div>
                <label className="text-slate-300 font-medium block mb-1">Permitted Marketing Statement</label>
                <textarea
                  required
                  rows="2"
                  placeholder="The exact statement verified by legal & brand teams."
                  value={newClaim.permitted_statement}
                  onChange={(e) => setNewClaim({ ...newClaim, permitted_statement: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-white"
                />
              </div>

              <div>
                <label className="text-slate-300 font-medium block mb-1">Mandatory Qualifiers & Footnotes</label>
                <input
                  type="text"
                  placeholder="e.g. Must include 'up to 20%' and test footnote."
                  value={newClaim.required_qualifiers}
                  onChange={(e) => setNewClaim({ ...newClaim, required_qualifiers: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-white"
                />
              </div>

              <div>
                <label className="text-slate-300 font-medium block mb-1">Supporting Approved Source (Optional)</label>
                <select
                  value={newClaim.source_version}
                  onChange={(e) => setNewClaim({ ...newClaim, source_version: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-white"
                >
                  <option value="">No linked source document</option>
                  {sources.flatMap((source) => (source.versions || [])
                    .filter((version) => version.is_currently_valid)
                    .map((version) => (
                      <option key={version.id} value={version.id}>
                        {source.document_code} — {source.title} [{version.version_label}]
                      </option>
                    )))}
                </select>
                <p className="text-slate-500 mt-1">
                  Link a current approved version to include its evidence with claim findings.
                </p>
              </div>

              <div>
                <label className="text-slate-300 font-medium block mb-1">Disallowed Exaggerations</label>
                <input
                  type="text"
                  placeholder="e.g. Guaranteed 50% savings"
                  value={newClaim.disallowed_variations}
                  onChange={(e) => setNewClaim({ ...newClaim, disallowed_variations: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-white"
                />
              </div>

              <div className="pt-2 flex justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setShowClaimModal(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 hover:bg-slate-700 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-medium cursor-pointer"
                >
                  Save Approved Claim
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* CREATE SOURCE MODAL */}
      {showSourceModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-lg rounded-2xl border border-slate-800 bg-[#0D1527] p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="font-bold text-white text-base">Register Source Document</h3>
              <button onClick={() => setShowSourceModal(false)} className="text-slate-400 hover:text-white cursor-pointer">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateSource} className="space-y-3.5 text-xs">
              <div>
                <label className="text-slate-300 font-medium block mb-1">Document Code</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. SRC-EV-2026-LAB"
                  value={newSource.document_code}
                  onChange={(e) => setNewSource({ ...newSource, document_code: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-white font-mono text-[11px]"
                />
              </div>

              <div>
                <label className="text-slate-300 font-medium block mb-1">Document Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. 2026 Field Reliability Benchmarks"
                  value={newSource.title}
                  onChange={(e) => setNewSource({ ...newSource, title: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-white"
                />
              </div>

              <div>
                <label className="text-slate-300 font-medium block mb-1">Description</label>
                <textarea
                  rows="3"
                  placeholder="Brief summary of trial methodology and sample size."
                  value={newSource.description}
                  onChange={(e) => setNewSource({ ...newSource, description: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-white"
                />
              </div>

              <div className="pt-2 flex justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setShowSourceModal(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 hover:bg-slate-700 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-medium cursor-pointer"
                >
                  Register Document
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {sourceVersionModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-2xl border border-slate-800 bg-[#0D1527] p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h3 className="font-bold text-white text-base">Add Approved Source Version</h3>
                <p className="text-xs text-slate-400 mt-1">
                  {sourceVersionModal.document_code} · {sourceVersionModal.title}
                </p>
              </div>
              <button onClick={() => setSourceVersionModal(null)} className="text-slate-400 hover:text-white cursor-pointer">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateSourceVersion} className="space-y-3.5 text-xs">
              <div>
                <label className="text-slate-300 font-medium block mb-1">Version Label</label>
                <input
                  type="text"
                  required
                  value={newSourceVersion.version_label}
                  onChange={(e) => setNewSourceVersion({ ...newSourceVersion, version_label: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-white"
                />
              </div>

              <div>
                <label className="text-slate-300 font-medium block mb-1">Full Approved Document Text</label>
                <textarea
                  required
                  rows="5"
                  value={newSourceVersion.full_text_content}
                  onChange={(e) => setNewSourceVersion({ ...newSourceVersion, full_text_content: e.target.value })}
                  placeholder="Paste the approved source text."
                  className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-white"
                />
              </div>

              <div>
                <label className="text-slate-300 font-medium block mb-1">Evidence Passages</label>
                <textarea
                  rows="4"
                  value={newSourceVersion.passage_texts}
                  onChange={(e) => setNewSourceVersion({ ...newSourceVersion, passage_texts: e.target.value })}
                  placeholder="Add one exact evidence excerpt per line."
                  className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-white"
                />
                <p className="text-slate-500 mt-1">Passage IDs will be assigned automatically (P1, P2, ...).</p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="text-slate-300 font-medium block mb-1">Effective Date (Optional)</label>
                  <input
                    type="date"
                    value={newSourceVersion.effective_date}
                    onChange={(e) => setNewSourceVersion({ ...newSourceVersion, effective_date: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-white"
                  />
                </div>
                <div>
                  <label className="text-slate-300 font-medium block mb-1">Expiration Date (Optional)</label>
                  <input
                    type="date"
                    value={newSourceVersion.expiration_date}
                    onChange={(e) => setNewSourceVersion({ ...newSourceVersion, expiration_date: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-white"
                  />
                </div>
              </div>

              <label className="inline-flex items-center gap-2 text-slate-300">
                <input
                  type="checkbox"
                  checked={newSourceVersion.is_approved}
                  onChange={(e) => setNewSourceVersion({ ...newSourceVersion, is_approved: e.target.checked })}
                  className="accent-emerald-500"
                />
                Approved for claim verification
              </label>

              <div className="pt-2 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setSourceVersionModal(null)}
                  className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 hover:bg-slate-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={savingSourceVersion}
                  className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-medium"
                >
                  {savingSourceVersion ? 'Saving...' : 'Save Source Version'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
