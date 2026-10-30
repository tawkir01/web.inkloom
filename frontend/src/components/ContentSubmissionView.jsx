import apiFetch from "../api";
import React, { useState } from 'react';
import { 
  Send, 
  Image as ImageIcon, 
  Sparkles, 
  CheckCircle2, 
  AlertCircle, 
  Briefcase
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function ContentSubmissionView({ onSubmitted }) {
  const { token, currentWorkspace } = useAuth();
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [rawText, setRawText] = useState('');
  const [imageFile, setImageFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [successResult, setSuccessResult] = useState(null);

  // Pre-configured problematic demo marketing copy samples
  const loadDemoSample = (type) => {
    if (type === 'ecovolt_problematic') {
      setTitle('EcoVolt Summer Savings Blast 2026');
      setDescription('Social media & digital banner copy');
      setRawText(
        'Switch your home power to ecovolt today! Our smart battery systems deliver guaranteed 50% savings ' +
        'on all monthly electricity bills for every homeowner in America. No special equipment needed.'
      );
    } else if (type === 'ecovolt_compliant') {
      setTitle('EcoVolt Verified Energy Copy');
      setDescription('Approved web landing page copy');
      setRawText(
        'Take control of your home utility costs with EcoVoltâ„¢ smart battery storage. ' +
        'Laboratory benchmark trials confirm homeowners save up to 20% on annual energy consumption ' +
        'when paired with our solar storage inverter. *Results vary by insulation and local utility rates.'
      );
    } else if (type === 'purenest_problematic') {
      setTitle('PureNest Eco-Clean Product Launch');
      setDescription('Retail packaging & promotional newsletter');
      setRawText(
        'PureNest multi-surface cleaner is 100% chemical-free and instantly destroys all household bacteria ' +
        'with zero natural residue. Safe for all fabrics.'
      );
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!currentWorkspace?.workspace_id) {
      setError('Please select an active workspace from the top navbar before submitting.');
      return;
    }

    setLoading(true);
    setError(null);
    setSuccessResult(null);

    try {
      const formData = new FormData();
      formData.append('title', title);
      formData.append('description', description);
      formData.append('raw_text', rawText);
      if (imageFile) {
        formData.append('image_file', imageFile);
      }

      const res = await apiFetch(`/api/workspaces/${currentWorkspace.workspace_id}/content/`, {
        method: 'POST',
        headers: {
          'Authorization': `Token ${token}`
        },
        body: formData
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || Object.values(data).flat().join(' '));
      }

      setSuccessResult(data);
      if (onSubmitted) {
        onSubmitted(data);
      }
    } catch (err) {
      setError(err.message || 'Failed to submit content.');
    } finally {
      setLoading(false);
    }
  };

  const wordCount = rawText.trim() ? rawText.trim().split(/\s+/).length : 0;
  const charCount = rawText.length;

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Title Header */}
      <div>
        <div className="flex items-center space-x-2">
          <h2 className="text-2xl font-bold text-white tracking-tight">Content Submission (Page 5)</h2>
          <span className="text-xs px-2.5 py-0.5 rounded-full bg-violet-950 text-violet-300 border border-violet-800/50">
            {currentWorkspace ? currentWorkspace.workspace_name : 'No Workspace'}
          </span>
        </div>
        <p className="text-xs text-slate-400 mt-1">
          Submit marketing copy and media for automated deterministic checks and evidence-backed governance analysis.
        </p>
      </div>

      {/* Demo Copy Helper Banner */}
      <div className="p-4 rounded-xl border border-violet-900/40 bg-gradient-to-r from-violet-950/30 via-[#0D1527] to-[#0D1527] space-y-2">
        <div className="flex items-center space-x-2 text-xs font-semibold text-violet-300">
          <Sparkles className="w-4 h-4 text-cyan-400" />
          <span>One-Click Test Samples (Demo Verification)</span>
        </div>
        <div className="flex flex-wrap gap-2 pt-1 text-xs">
          <button
            type="button"
            onClick={() => loadDemoSample('ecovolt_problematic')}
            className="px-3 py-1.5 rounded-lg border border-red-800/60 bg-red-950/30 text-red-300 hover:bg-red-900/40 transition cursor-pointer"
          >
            âš¡ EcoVolt Problematic (Exaggerated "50% guaranteed")
          </button>
          <button
            type="button"
            onClick={() => loadDemoSample('ecovolt_compliant')}
            className="px-3 py-1.5 rounded-lg border border-emerald-800/60 bg-emerald-950/30 text-emerald-300 hover:bg-emerald-900/40 transition cursor-pointer"
          >
            âœ“ EcoVolt Compliant ("Save up to 20%")
          </button>
          <button
            type="button"
            onClick={() => loadDemoSample('purenest_problematic')}
            className="px-3 py-1.5 rounded-lg border border-amber-800/60 bg-amber-950/30 text-amber-300 hover:bg-amber-900/40 transition cursor-pointer"
          >
            ðŸŒ¿ PureNest Problematic ("100% chemical-free")
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-950/40 border border-red-800/60 text-red-300 text-xs flex items-start space-x-2.5">
          <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {successResult && (
        <div className="p-5 rounded-xl bg-emerald-950/30 border border-emerald-800/50 space-y-2">
          <div className="flex items-center space-x-2 text-emerald-300 font-semibold text-sm">
            <CheckCircle2 className="w-5 h-5 text-emerald-400" />
            <span>Submission Created Successfully: v1 (Version Snapshot Initialized)</span>
          </div>
          <p className="text-xs text-slate-300">
            Immutable SHA-256 Hash:{' '}
            <code className="text-emerald-400 font-mono text-[11px] bg-slate-900 px-2 py-0.5 rounded">
              {successResult.versions?.[0]?.checksum_sha256}
            </code>
          </p>
        </div>
      )}

      {/* Submission Form */}
      <form onSubmit={handleSubmit} className="rounded-2xl border border-slate-800 bg-[#0D1527]/80 p-6 md:p-8 space-y-6">
        {/* Title */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold uppercase tracking-wider text-slate-300">
            Content Asset Title <span className="text-red-400">*</span>
          </label>
          <input
            type="text"
            required
            placeholder="e.g. Summer 2026 Solar Email Campaign"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-700/80 text-white placeholder-slate-500 focus:outline-none focus:border-violet-500 text-sm"
          />
        </div>

        {/* Description */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold uppercase tracking-wider text-slate-300">
            Campaign Objective / Channel (Optional)
          </label>
          <input
            type="text"
            placeholder="e.g. Paid LinkedIn Ad, Packaging Print Copy, Press Release"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-700/80 text-white placeholder-slate-500 focus:outline-none focus:border-violet-500 text-sm"
          />
        </div>

        {/* Marketing Copy Textarea */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-300">
              Marketing Copy Text <span className="text-red-400">*</span>
            </label>
            <span className="text-[11px] text-slate-500 font-mono">
              {wordCount} words â€¢ {charCount} chars
            </span>
          </div>

          <textarea
            required
            rows="7"
            placeholder="Paste your marketing copy here for brand guidelines and claim verification..."
            value={rawText}
            onChange={(e) => setRawText(e.target.value)}
            className="w-full p-4 rounded-xl bg-slate-900 border border-slate-700/80 text-white placeholder-slate-500 focus:outline-none focus:border-violet-500 text-sm leading-relaxed"
          />
        </div>

        {/* Optional Image Upload */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold uppercase tracking-wider text-slate-300">
            Optional Marketing Visual / Image Asset (Supported in Phase 10 OCR)
          </label>
          <div className="p-4 rounded-xl border border-dashed border-slate-700 bg-slate-900/50 flex flex-col items-center justify-center space-y-2 text-center text-xs">
            <ImageIcon className="w-6 h-6 text-slate-500" />
            <div className="text-slate-300">
              <label className="text-violet-400 hover:text-violet-300 cursor-pointer font-medium">
                Click to browse files
                <input
                  type="file"
                  accept="image/png, image/jpeg, image/webp"
                  onChange={(e) => setImageFile(e.target.files[0] || null)}
                  className="hidden"
                />
              </label>
              {' '}or drag image here
            </div>
            {imageFile ? (
              <span className="text-xs text-emerald-400 font-mono">Selected: {imageFile.name}</span>
            ) : (
              <span className="text-[10px] text-slate-500">PNG, JPG, or WEBP up to 10MB</span>
            )}
          </div>
        </div>

        {/* Submit Action */}
        <div className="pt-2 flex items-center justify-between border-t border-slate-800">
          <div className="text-[11px] text-slate-400 flex items-center space-x-1.5">
            <Briefcase className="w-3.5 h-3.5 text-cyan-400" />
            <span>Target Workspace: <strong className="text-slate-200">{currentWorkspace?.workspace_name}</strong></span>
          </div>

          <button
            type="submit"
            disabled={loading || !rawText.trim()}
            className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white font-medium text-xs shadow-lg shadow-violet-600/30 transition flex items-center space-x-2 cursor-pointer disabled:opacity-50"
          >
            <span>{loading ? 'Submitting & Hash Computing...' : 'Submit Content (Spawn v1)'}</span>
            <Send className="w-3.5 h-3.5" />
          </button>
        </div>
      </form>
    </div>
  );
}
