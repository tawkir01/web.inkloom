import apiFetch from "../api";
/**
 * ReviewWorkspaceView.jsx â€” Page 6: AI Review Workspace
 * ======================================================
 *
 * This is the core operational screen of Inkloom Guardian.
 *
 * WHAT THIS PAGE DOES (beginner-friendly explanation):
 * â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
 * When a content creator submits marketing copy, a Brand Reviewer uses
 * this page to:
 *
 *   1. SELECT a submitted content item from the workspace
 *   2. SELECT which version to review (v1, v2, v3...)
 *   3. CLICK "Run Governance Review" â€” this calls the backend rule engine
 *      which scans the copy and returns findings (problems and verifications)
 *   4. READ the flagged text highlighted in the left panel (the submitted copy)
 *      with the exact problematic spans visually marked
 *   5. READ the evidence-linked explanations in the right panel (findings)
 *      filtered by severity: CRITICAL â†’ HIGH â†’ MEDIUM â†’ LOW
 *   6. APPROVE or REJECT or REQUEST CHANGES via the approval decision panel
 *   7. ADD COMMENTS linked to specific findings for collaborative feedback
 *
 * LAYOUT:
 *   â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
 *   â”‚  LEFT PANEL                 â”‚  RIGHT PANEL                   â”‚
 *   â”‚  â€¢ Version selector         â”‚  â€¢ Review Run Stats            â”‚
 *   â”‚  â€¢ Submitted copy text      â”‚  â€¢ Findings list (filterable)  â”‚
 *   â”‚  â€¢ Highlighted spans        â”‚  â€¢ Evidence passages           â”‚
 *   â”‚  â€¢ Approval decision panel  â”‚  â€¢ Comment threads             â”‚
 *   â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
 */

import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';

// â”€â”€â”€ Severity badge color map â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
const SEVERITY_COLORS = {
  CRITICAL: { bg: '#ff1a1a22', border: '#ff1a1a', text: '#ff4d4d', dot: '#ff1a1a' },
  HIGH:     { bg: '#ff6b0022', border: '#ff6b00', text: '#ff8c33', dot: '#ff6b00' },
  MEDIUM:   { bg: '#ffd70022', border: '#ffd700', text: '#ffe033', dot: '#ffd700' },
  LOW:      { bg: '#00c85222', border: '#00c852', text: '#33d96a', dot: '#00c852' },
};

// â”€â”€â”€ Verification status config â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
const VERIFICATION_STATUS_CONFIG = {
  SUPPORTED:           { color: '#00c852', icon: 'âœ“', label: 'Supported by Source' },
  CONTRADICTED:        { color: '#ff4d4d', icon: 'âœ—', label: 'Contradicts Policy' },
  UNSUPPORTED:         { color: '#ffd700', icon: 'âš ', label: 'Unsupported' },
  UNABLE_TO_DETERMINE: { color: '#8888aa', icon: '?', label: 'Ambiguous' },
};

// â”€â”€â”€ Highlighted text renderer â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
function HighlightedText({ text, findings, activeFindingId, onFindingClick }) {
  /**
   * This component takes plain text and a list of findings,
   * then renders the text with colored highlights over the flagged spans.
   *
   * Think of it like Google Docs with inline comment markers.
   *
   * HOW IT WORKS:
   *  1. Sort all findings by their start_char position
   *  2. Walk through the text character by character
   *  3. When we hit a finding's start_char, switch to highlighted mode
   *  4. When we hit end_char, switch back to normal mode
   */
  if (!text) return <p style={{ color: '#8888aa', fontStyle: 'italic' }}>No text available.</p>;
   const characters = Array.from(text);

   // Build a list of segments: { text, finding? }
  const blockFindings = findings.filter(
    f => f.start_char != null && f.end_char != null && f.start_char < f.end_char
  );

  // Sort by start position
  const sorted = [...blockFindings].sort((a, b) => a.start_char - b.start_char);

  // Merge overlapping spans and build segments
  const segments = [];
  let pos = 0;

  for (const f of sorted) {
    const start = Math.max(pos, f.start_char);
    const end = Math.min(characters.length, f.end_char);
    if (start >= characters.length) break;

    // Unchanged text before this finding
    if (start > pos) {
      segments.push({ text: characters.slice(pos, start).join(''), finding: null });
    }

    if (end > start) {
      segments.push({ text: characters.slice(start, end).join(''), finding: f });
      pos = end;
    }
  }

  // Remainder after all findings
  if (pos < characters.length) {
    segments.push({ text: characters.slice(pos).join(''), finding: null });
  }

  // If no findings overlap this text, just render it plain
  if (segments.length === 0) {
    return (
      <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word', margin: 0,
        fontFamily: 'inherit', lineHeight: '1.8', color: '#c8c8e0' }}>
        {text}
      </pre>
    );
  }

  return (
    <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word', margin: 0,
      fontFamily: 'inherit', lineHeight: '1.8', color: '#c8c8e0' }}>
      {segments.map((seg, i) => {
        if (!seg.finding) {
          return <span key={i}>{seg.text}</span>;
        }
        const sev = seg.finding.severity;
        const colors = SEVERITY_COLORS[sev] || SEVERITY_COLORS.MEDIUM;
        const isActive = seg.finding.id === activeFindingId;

        return (
          <mark
            key={i}
            onClick={() => onFindingClick(seg.finding.id)}
            title={seg.finding.category}
            style={{
              backgroundColor: isActive ? colors.border + '55' : colors.bg,
              borderBottom: `2px solid ${colors.border}`,
              borderRadius: '3px',
              padding: '1px 2px',
              cursor: 'pointer',
              transition: 'background 0.2s',
              color: '#e8e8f8',
              position: 'relative',
            }}
          >
            {seg.text}
            <sup style={{
              fontSize: '9px',
              color: colors.text,
              fontWeight: 700,
              marginLeft: '2px',
              verticalAlign: 'super',
            }}>
              {sev[0]}
            </sup>
          </mark>
        );
      })}
    </pre>
  );
}

// â”€â”€â”€ Finding Card â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
function FindingCard({ finding, isActive, onClick }) {
  const colors = SEVERITY_COLORS[finding.severity] || SEVERITY_COLORS.MEDIUM;
  const vsConfig = VERIFICATION_STATUS_CONFIG[finding.verification_status] || VERIFICATION_STATUS_CONFIG.UNABLE_TO_DETERMINE;
  const [expanded, setExpanded] = useState(false);

  return (
    <div
      onClick={() => { onClick(finding.id); setExpanded(!expanded); }}
      style={{
        background: isActive ? colors.bg : 'rgba(255,255,255,0.03)',
        border: `1px solid ${isActive ? colors.border : 'rgba(255,255,255,0.08)'}`,
        borderLeft: `4px solid ${colors.border}`,
        borderRadius: '10px',
        padding: '14px 16px',
        cursor: 'pointer',
        transition: 'all 0.25s ease',
        marginBottom: '10px',
      }}
    >
      {/* Header Row */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
        {/* Severity badge */}
        <span style={{
          background: colors.border,
          color: '#0a0a1e',
          fontSize: '10px',
          fontWeight: 800,
          padding: '2px 8px',
          borderRadius: '20px',
          letterSpacing: '0.5px',
        }}>
          {finding.severity}
        </span>

        {/* Verification status */}
        <span style={{
          color: vsConfig.color,
          fontSize: '11px',
          fontWeight: 600,
          display: 'flex',
          alignItems: 'center',
          gap: '3px',
        }}>
          {vsConfig.icon} {vsConfig.label}
        </span>

        {/* Citation validated badge */}
        {finding.is_citation_validated && (
          <span style={{
            marginLeft: 'auto',
            fontSize: '10px',
            color: '#00c852',
            background: '#00c85215',
            border: '1px solid #00c85240',
            padding: '1px 6px',
            borderRadius: '10px',
          }}>
            âœ“ DB-Verified
          </span>
        )}
      </div>

      {/* Category */}
      <div style={{ fontSize: '11px', color: '#8888aa', marginBottom: '4px', fontWeight: 600 }}>
        {finding.category}
      </div>

      {/* Flagged Text */}
      {finding.flagged_text && !finding.flagged_text.startsWith('[Entire') && (
        <div style={{
          background: 'rgba(0,0,0,0.25)',
          borderRadius: '6px',
          padding: '6px 10px',
          marginBottom: '8px',
          fontFamily: 'monospace',
          fontSize: '12px',
          color: colors.text,
          wordBreak: 'break-word',
        }}>
          "{finding.flagged_text.slice(0, 100)}{finding.flagged_text.length > 100 ? '...' : ''}"
        </div>
      )}

      {/* Explanation */}
      <p style={{ fontSize: '12px', color: '#a8a8c0', margin: '0 0 6px 0', lineHeight: '1.5' }}>
        {finding.explanation}
      </p>

      {/* Expanded details */}
      {expanded && (
        <div style={{
          borderTop: '1px solid rgba(255,255,255,0.08)',
          marginTop: '10px',
          paddingTop: '10px',
          animation: 'fadeIn 0.2s ease',
        }}>
          {/* Source evidence */}
          {finding.quoted_passage && (
            <div style={{
              background: 'rgba(0,200,82,0.06)',
              border: '1px solid rgba(0,200,82,0.2)',
              borderRadius: '8px',
              padding: '10px',
              marginBottom: '8px',
            }}>
              <div style={{ fontSize: '10px', color: '#00c852', fontWeight: 700, marginBottom: '4px' }}>
                ðŸ“„ {finding.source_version
                  ? 'SOURCE EVIDENCE'
                  : finding.approved_claim_title
                    ? 'APPROVED CLAIM WORDING'
                    : 'EVIDENCE'}
                {finding.source_document_code && (
                  <span style={{ color: '#8888aa', fontWeight: 400, marginLeft: '6px' }}>
                    {finding.source_document_code}: {finding.source_document_title} [{finding.source_version_label}]
                  </span>
                )}
                {finding.source_passage_id && (
                  <span style={{ color: '#8888aa', fontWeight: 400, marginLeft: '6px' }}>
                    Passage: {finding.source_passage_id}
                  </span>
                )}
                {finding.brand_rule_name && (
                  <span style={{ color: '#8888aa', fontWeight: 400, marginLeft: '6px' }}>
                    Brand Rule: {finding.brand_rule_name}
                  </span>
                )}
                {finding.approved_claim_title && (
                  <span style={{ color: '#8888aa', fontWeight: 400, marginLeft: '6px' }}>
                    Claim: {finding.approved_claim_title}
                  </span>
                )}
              </div>
              <p style={{ fontSize: '12px', color: '#c8c8e0', margin: 0, lineHeight: '1.6', fontStyle: 'italic' }}>
                "{finding.quoted_passage.slice(0, 400)}{finding.quoted_passage.length > 400 ? '...' : ''}"
              </p>
            </div>
          )}

          {/* Suggested correction */}
          {finding.suggested_correction && (
            <div style={{
              background: 'rgba(100,100,255,0.06)',
              border: '1px solid rgba(100,100,255,0.2)',
              borderRadius: '8px',
              padding: '10px',
            }}>
              <div style={{ fontSize: '10px', color: '#8888ff', fontWeight: 700, marginBottom: '4px' }}>
                ðŸ’¡ SUGGESTED CORRECTION
              </div>
              <p style={{ fontSize: '12px', color: '#c8c8e0', margin: 0, lineHeight: '1.5' }}>
                {finding.suggested_correction}
              </p>
            </div>
          )}

          {/* Confidence */}
          {finding.confidence != null && (
            <div style={{ marginTop: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '10px', color: '#8888aa' }}>Confidence:</span>
              <div style={{
                height: '4px', width: '100px',
                background: 'rgba(255,255,255,0.1)', borderRadius: '2px', overflow: 'hidden'
              }}>
                <div style={{
                  height: '100%', width: `${finding.confidence * 100}%`,
                  background: colors.border, borderRadius: '2px',
                }} />
              </div>
              <span style={{ fontSize: '10px', color: colors.text }}>
                {Math.round(finding.confidence * 100)}%
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// â”€â”€â”€ Main Page Component â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
export default function ReviewWorkspaceView() {
  const { user, currentWorkspace, token } = useAuth();
  const canApprove = ['BRAND_REVIEWER', 'AGENCY_ADMIN'].includes(currentWorkspace?.role);

  // Data state
  const [contentItems, setContentItems] = useState([]);
  const [selectedItem, setSelectedItem] = useState(null);
  const [selectedVersion, setSelectedVersion] = useState(null);
  const [reviewRun, setReviewRun] = useState(null);

  // UI state
  const [loading, setLoading] = useState(false);
  const [runningReview, setRunningReview] = useState(false);
  const [activeFindingId, setActiveFindingId] = useState(null);
  const [severityFilter, setSeverityFilter] = useState('ALL');
  const [findingTypeFilter, setFindingTypeFilter] = useState('ALL');
  const [error, setError] = useState('');

  // Approval state
  const [approvalDecision, setApprovalDecision] = useState('');
  const [approvalNotes, setApprovalNotes] = useState('');
  const [submittingApproval, setSubmittingApproval] = useState(false);
  const [approvalSuccess, setApprovalSuccess] = useState('');

  // Comment state
  const [commentText, setCommentText] = useState('');
  const [comments, setComments] = useState([]);
  const [commentFindingId, setCommentFindingId] = useState('');

  const api = useCallback(async (path, options = {}) => {
    const res = await apiFetch(`/api${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Token ${token}`,
        ...options.headers,
      },
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || JSON.stringify(data));
    return data;
  }, [token]);

  // Load content items when workspace changes
  useEffect(() => {
    if (!currentWorkspace?.workspace_id) return;
    setLoading(true);
    setSelectedItem(null);
    setSelectedVersion(null);
    setReviewRun(null);
    api(`/workspaces/${currentWorkspace.workspace_id}/content/`)
      .then(data => setContentItems(data))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [currentWorkspace?.workspace_id, api]);

  // Load past review runs when a version is selected
  const loadReviewHistory = useCallback(async (item, versionNum) => {
    try {
      const runs = await api(`/content/${item.id}/versions/${versionNum}/reviews/`);
      if (runs.length > 0) {
        setReviewRun(runs[0]); // Show most recent run
      } else {
        setReviewRun(null);
      }
    } catch {}

    try {
      const coms = await api(`/content/${item.id}/versions/${versionNum}/comments/`);
      setComments(coms);
    } catch {}
  }, [api]);

  const handleSelectItem = (item) => {
    setSelectedItem(item);
    setReviewRun(null);
    setComments([]);
    setActiveFindingId(null);
    setApprovalSuccess('');
    setError('');

    // Auto-select latest version
    const versions = item.versions || [];
    if (versions.length > 0) {
      const latest = versions[0]; // ordered by -version_number
      setSelectedVersion(latest);
      loadReviewHistory(item, latest.version_number);
    }
  };

  const handleSelectVersion = (version) => {
    setSelectedVersion(version);
    setReviewRun(null);
    setActiveFindingId(null);
    setApprovalSuccess('');
    loadReviewHistory(selectedItem, version.version_number);
  };

  const handleRunReview = async () => {
    if (!selectedItem || !selectedVersion) return;
    setRunningReview(true);
    setError('');
    try {
      const run = await api(
        `/content/${selectedItem.id}/versions/${selectedVersion.version_number}/review/`,
        { method: 'POST' }
      );
      setReviewRun(run);
      // Refresh the version status in selectedVersion
      const updatedItems = await api(`/workspaces/${currentWorkspace.workspace_id}/content/`);
      setContentItems(updatedItems);
      const updatedItem = updatedItems.find(i => i.id === selectedItem.id);
      if (updatedItem) {
        setSelectedItem(updatedItem);
        const updatedVersion = updatedItem.versions?.find(v => v.version_number === selectedVersion.version_number);
        if (updatedVersion) setSelectedVersion(updatedVersion);
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setRunningReview(false);
    }
  };

  const handleApprovalSubmit = async () => {
    if (!approvalDecision || !selectedItem || !selectedVersion) return;
    setSubmittingApproval(true);
    setError('');
    try {
      await api(
        `/content/${selectedItem.id}/versions/${selectedVersion.version_number}/approval/`,
        {
          method: 'POST',
          body: JSON.stringify({ decision: approvalDecision, decision_notes: approvalNotes }),
        }
      );
      setApprovalSuccess(`Decision recorded: ${approvalDecision}`);
      setApprovalDecision('');
      setApprovalNotes('');
      // Refresh version status
      const updatedItems = await api(`/workspaces/${currentWorkspace.workspace_id}/content/`);
      setContentItems(updatedItems);
      const updatedItem = updatedItems.find(i => i.id === selectedItem.id);
      if (updatedItem) {
        setSelectedItem(updatedItem);
        const uv = updatedItem.versions?.find(v => v.version_number === selectedVersion.version_number);
        if (uv) setSelectedVersion(uv);
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setSubmittingApproval(false);
    }
  };

  const handleCommentSubmit = async () => {
    if (!commentText.trim() || !selectedItem || !selectedVersion) return;
    try {
      const payload = { comment_text: commentText };
      if (commentFindingId) payload.finding_id = commentFindingId;
      const newComment = await api(
        `/content/${selectedItem.id}/versions/${selectedVersion.version_number}/comments/`,
        { method: 'POST', body: JSON.stringify(payload) }
      );
      setComments(prev => [...prev, newComment]);
      setCommentText('');
      setCommentFindingId('');
    } catch (e) {
      setError(e.message);
    }
  };

  // Filter findings based on UI controls
  const allFindings = reviewRun?.findings || [];
  const filteredFindings = allFindings.filter(f => {
    const sevOk = severityFilter === 'ALL' || f.severity === severityFilter;
    const typeOk = findingTypeFilter === 'ALL' || f.finding_type === findingTypeFilter;
    return sevOk && typeOk;
  });
  const ocrText = selectedVersion?.extracted_ocr_text || '';
  const ocrOffset = Array.from(selectedVersion?.raw_text || '').length + 1;
  const ocrEnd = ocrOffset + Array.from(ocrText).length;
  const ocrFindings = filteredFindings.flatMap(f => {
    if (f.start_char == null || f.end_char == null) return [];
    const start = Math.max(f.start_char, ocrOffset);
    const end = Math.min(f.end_char, ocrEnd);
    return end > start
      ? [{ ...f, start_char: start - ocrOffset, end_char: end - ocrOffset }]
      : [];
  });

  // Stat counts
  const counts = {
    CRITICAL: allFindings.filter(f => f.severity === 'CRITICAL').length,
    HIGH: allFindings.filter(f => f.severity === 'HIGH').length,
    MEDIUM: allFindings.filter(f => f.severity === 'MEDIUM').length,
    LOW: allFindings.filter(f => f.severity === 'LOW').length,
  };

  const statusBadge = (version) => {
    const map = {
      SUBMITTED:         ['#8888aa', '#8888aa22', 'Submitted'],
      PROCESSING:        ['#6464ff', '#6464ff22', 'Processing'],
      NEEDS_CHANGES:     ['#ff6b00', '#ff6b0022', 'Needs Changes'],
      READY_FOR_REVIEW:  ['#ffd700', '#ffd70022', 'Ready for Review'],
      APPROVED:          ['#00c852', '#00c85222', 'Approved'],
      REJECTED:          ['#ff4d4d', '#ff4d4d22', 'Rejected'],
      FAILED:            ['#ff4d4d', '#ff4d4d22', 'Failed'],
      DRAFT:             ['#6464aa', '#6464aa22', 'Draft'],
    };
    const [color, bg, label] = map[version.status] || ['#8888aa', '#8888aa22', version.status];
    return (
      <span style={{
        background: bg, color, border: `1px solid ${color}40`,
        padding: '2px 8px', borderRadius: '20px', fontSize: '11px', fontWeight: 700,
      }}>{label}</span>
    );
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #0a0a1e 0%, #12122e 40%, #0d0d2b 100%)',
      color: '#e8e8f8',
      fontFamily: "'Inter', 'Segoe UI', sans-serif",
      padding: '24px',
    }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        @keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.5; } }
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.15); border-radius: 3px; }
        button:focus { outline: 2px solid #6464ff; outline-offset: 2px; }
      `}</style>

      {/* â”€â”€ PAGE HEADER â”€â”€ */}
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{
          fontSize: '26px', fontWeight: 800, margin: 0,
          background: 'linear-gradient(135deg, #e8e8f8, #8888cc)',
          WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
        }}>
          âš–ï¸ Governance Review Workspace
        </h1>
        <p style={{ color: '#8888aa', fontSize: '14px', margin: '6px 0 0' }}>
          Run deterministic brand governance checks Â· Review evidence-linked findings Â· Make binding approval decisions
        </p>
      </div>

      {!currentWorkspace && (
        <div style={{
          background: 'rgba(255,107,0,0.1)', border: '1px solid rgba(255,107,0,0.3)',
          borderRadius: '12px', padding: '20px', textAlign: 'center', color: '#ff8c33',
        }}>
          âš ï¸ Please select a workspace from the top navigation to continue.
        </div>
      )}

      {currentWorkspace && (
        <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr 420px', gap: '20px', alignItems: 'start' }}>

          {/* â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ LEFT SIDEBAR: Content Item Selector â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */}
          <div style={{
            background: 'rgba(255,255,255,0.04)',
            border: '1px solid rgba(255,255,255,0.08)',
            borderRadius: '16px',
            padding: '16px',
            maxHeight: 'calc(100vh - 160px)',
            overflowY: 'auto',
          }}>
            <h3 style={{ margin: '0 0 14px', fontSize: '13px', fontWeight: 700, color: '#8888cc', letterSpacing: '0.5px' }}>
              CONTENT ITEMS
            </h3>

            {loading && (
              <div style={{ color: '#8888aa', fontSize: '13px', textAlign: 'center', padding: '20px' }}>
                <span style={{ animation: 'pulse 1.5s infinite' }}>Loading...</span>
              </div>
            )}

            {contentItems.length === 0 && !loading && (
              <p style={{ color: '#6666aa', fontSize: '12px', textAlign: 'center', padding: '20px' }}>
                No content submitted yet. Go to "Submit Content" to create some.
              </p>
            )}

            {contentItems.map(item => (
              <div
                key={item.id}
                onClick={() => handleSelectItem(item)}
                style={{
                  padding: '10px 12px',
                  marginBottom: '6px',
                  borderRadius: '10px',
                  cursor: 'pointer',
                  background: selectedItem?.id === item.id
                    ? 'rgba(100,100,255,0.15)' : 'rgba(255,255,255,0.03)',
                  border: `1px solid ${selectedItem?.id === item.id ? 'rgba(100,100,255,0.4)' : 'rgba(255,255,255,0.06)'}`,
                  transition: 'all 0.2s',
                }}
              >
                <div style={{ fontSize: '13px', fontWeight: 600, color: '#e8e8f8', marginBottom: '4px' }}>
                  {item.title}
                </div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span style={{ fontSize: '11px', color: '#8888aa' }}>
                    {item.versions_count} version{item.versions_count !== 1 ? 's' : ''}
                  </span>
                  {item.latest_version && statusBadge(item.latest_version)}
                </div>
              </div>
            ))}
          </div>

          {/* â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ CENTER PANEL: Copy + Highlights â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>

            {/* Version selector */}
            {selectedItem && (
              <div style={{
                background: 'rgba(255,255,255,0.04)',
                border: '1px solid rgba(255,255,255,0.08)',
                borderRadius: '16px',
                padding: '16px',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
                  <h3 style={{ margin: 0, fontSize: '14px', fontWeight: 700, color: '#c8c8e0' }}>
                    {selectedItem.title}
                  </h3>
                  {selectedVersion && statusBadge(selectedVersion)}
                </div>

                {/* Version tabs */}
                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '14px' }}>
                  {(selectedItem.versions || []).map(v => (
                    <button
                      key={v.id}
                      onClick={() => handleSelectVersion(v)}
                      style={{
                        padding: '5px 14px',
                        borderRadius: '20px',
                        border: '1px solid',
                        borderColor: selectedVersion?.id === v.id ? '#6464ff' : 'rgba(255,255,255,0.15)',
                        background: selectedVersion?.id === v.id ? 'rgba(100,100,255,0.2)' : 'transparent',
                        color: selectedVersion?.id === v.id ? '#9999ff' : '#a8a8c0',
                        fontSize: '12px',
                        fontWeight: 600,
                        cursor: 'pointer',
                        transition: 'all 0.2s',
                      }}
                    >
                      v{v.version_number}
                    </button>
                  ))}
                </div>

                {/* Run Review button */}
                <button
                  onClick={handleRunReview}
                  disabled={runningReview || !selectedVersion}
                  id="btn-run-review"
                  style={{
                    width: '100%',
                    padding: '12px',
                    borderRadius: '10px',
                    border: 'none',
                    background: runningReview
                      ? 'rgba(100,100,255,0.3)'
                      : 'linear-gradient(135deg, #4040cc, #6464ff)',
                    color: '#fff',
                    fontWeight: 700,
                    fontSize: '14px',
                    cursor: runningReview ? 'not-allowed' : 'pointer',
                    transition: 'all 0.2s',
                    boxShadow: runningReview ? 'none' : '0 4px 20px rgba(100,100,255,0.3)',
                  }}
                >
                  {runningReview
                    ? 'â³ Running Governance Review...'
                    : 'ðŸ” Run Governance Review'}
                </button>
              </div>
            )}

            {/* Highlighted copy display */}
            {selectedVersion && (
              <div style={{
                background: 'rgba(255,255,255,0.04)',
                border: '1px solid rgba(255,255,255,0.08)',
                borderRadius: '16px',
                padding: '20px',
                flex: 1,
              }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
                  <h3 style={{ margin: 0, fontSize: '13px', fontWeight: 700, color: '#8888cc', letterSpacing: '0.5px' }}>
                    SUBMITTED COPY â€” v{selectedVersion.version_number}
                  </h3>
                  <span style={{ fontSize: '10px', color: '#6666aa', fontFamily: 'monospace' }}>
                    SHA: {selectedVersion.checksum_sha256?.slice(0, 12)}...
                  </span>
                </div>

                <HighlightedText
                  text={selectedVersion.raw_text}
                  findings={filteredFindings}
                  activeFindingId={activeFindingId}
                  onFindingClick={setActiveFindingId}
                />

                {selectedVersion.extracted_ocr_text && (
                  <div style={{ marginTop: '16px', borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: '12px' }}>
                    <div style={{ fontSize: '11px', color: '#8888aa', marginBottom: '8px', fontWeight: 700 }}>
                      OCR EXTRACTED TEXT
                    </div>
                    <HighlightedText
                      text={selectedVersion.extracted_ocr_text}
                      findings={ocrFindings}
                      activeFindingId={activeFindingId}
                      onFindingClick={setActiveFindingId}
                    />
                  </div>
                )}
              </div>
            )}

            {/* Approval decision panel */}
            {selectedVersion && selectedVersion.status !== 'APPROVED' && canApprove && (
              <div style={{
                background: 'rgba(255,255,255,0.04)',
                border: '1px solid rgba(255,255,255,0.08)',
                borderRadius: '16px',
                padding: '16px',
              }}>
                <h3 style={{ margin: '0 0 12px', fontSize: '13px', fontWeight: 700, color: '#8888cc', letterSpacing: '0.5px' }}>
                  APPROVAL DECISION
                  <span style={{ marginLeft: '8px', fontSize: '11px', color: '#6666aa', fontWeight: 400 }}>
                    (Brand Reviewer / Admin only)
                  </span>
                </h3>

                {approvalSuccess && (
                  <div style={{
                    background: 'rgba(0,200,82,0.1)', border: '1px solid rgba(0,200,82,0.3)',
                    borderRadius: '8px', padding: '10px', marginBottom: '12px',
                    color: '#00c852', fontSize: '13px', fontWeight: 600,
                  }}>
                    âœ“ {approvalSuccess}
                  </div>
                )}

                {selectedVersion && selectedVersion.status !== 'APPROVED' && !canApprove && (
                  <div style={{
                    background: 'rgba(255,215,0,0.05)',
                    border: '1px solid rgba(255,215,0,0.18)',
                    borderRadius: '12px',
                    padding: '12px',
                    color: '#b8b08a',
                    fontSize: '12px',
                    lineHeight: '1.5',
                  }}>
                    You can review findings and comment on this version. Approval decisions are available to Brand Reviewers and Agency Administrators.
                  </div>
                )}

                <div style={{ display: 'flex', gap: '8px', marginBottom: '10px' }}>
                  {[
                    { value: 'APPROVED', label: 'âœ“ Approve', color: '#00c852' },
                    { value: 'CHANGES_REQUESTED', label: 'â†© Request Changes', color: '#ffd700' },
                    { value: 'REJECTED', label: 'âœ— Reject', color: '#ff4d4d' },
                  ].map(opt => (
                    <button
                      key={opt.value}
                      onClick={() => setApprovalDecision(opt.value)}
                      id={`btn-decision-${opt.value.toLowerCase()}`}
                      style={{
                        flex: 1,
                        padding: '9px 6px',
                        borderRadius: '8px',
                        border: `1px solid ${approvalDecision === opt.value ? opt.color : 'rgba(255,255,255,0.1)'}`,
                        background: approvalDecision === opt.value ? opt.color + '22' : 'transparent',
                        color: approvalDecision === opt.value ? opt.color : '#8888aa',
                        fontWeight: 700,
                        fontSize: '12px',
                        cursor: 'pointer',
                        transition: 'all 0.2s',
                      }}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>

                <textarea
                  value={approvalNotes}
                  onChange={e => setApprovalNotes(e.target.value)}
                  placeholder="Decision notes / rationale (optional)..."
                  id="input-approval-notes"
                  rows={2}
                  style={{
                    width: '100%', background: 'rgba(0,0,0,0.3)',
                    border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px',
                    color: '#e8e8f8', padding: '10px', fontSize: '13px',
                    resize: 'vertical', fontFamily: 'inherit', boxSizing: 'border-box',
                    marginBottom: '10px',
                  }}
                />

                <button
                  onClick={handleApprovalSubmit}
                  disabled={!approvalDecision || submittingApproval}
                  id="btn-submit-approval"
                  style={{
                    width: '100%', padding: '10px',
                    borderRadius: '8px', border: 'none',
                    background: approvalDecision
                      ? 'linear-gradient(135deg, #3333aa, #5555cc)'
                      : 'rgba(255,255,255,0.08)',
                    color: approvalDecision ? '#fff' : '#6666aa',
                    fontWeight: 700, fontSize: '13px',
                    cursor: approvalDecision ? 'pointer' : 'not-allowed',
                    transition: 'all 0.2s',
                  }}
                >
                  {submittingApproval ? 'Submitting...' : 'Submit Decision'}
                </button>
              </div>
            )}

            {selectedVersion?.status === 'APPROVED' && (
              <div style={{
                background: 'rgba(0,200,82,0.08)', border: '1px solid rgba(0,200,82,0.3)',
                borderRadius: '16px', padding: '16px', textAlign: 'center',
              }}>
                <div style={{ fontSize: '24px', marginBottom: '4px' }}>âœ…</div>
                <div style={{ fontWeight: 700, color: '#00c852', fontSize: '15px' }}>Version Approved</div>
                <div style={{ color: '#8888aa', fontSize: '12px', marginTop: '4px' }}>
                  This exact version snapshot is approved and locked.
                  Any revision creates a new version requiring fresh approval.
                </div>
              </div>
            )}

            {error && (
              <div style={{
                background: 'rgba(255,77,77,0.1)', border: '1px solid rgba(255,77,77,0.3)',
                borderRadius: '10px', padding: '12px', color: '#ff4d4d', fontSize: '13px',
              }}>
                âš  {error}
              </div>
            )}

            {!selectedItem && (
              <div style={{
                textAlign: 'center', padding: '60px 20px',
                background: 'rgba(255,255,255,0.02)', border: '1px dashed rgba(255,255,255,0.1)',
                borderRadius: '16px', color: '#6666aa',
              }}>
                <div style={{ fontSize: '40px', marginBottom: '12px' }}>ðŸ“‹</div>
                <div style={{ fontWeight: 600, fontSize: '15px', marginBottom: '6px', color: '#8888aa' }}>
                  Select a Content Item
                </div>
                <div style={{ fontSize: '13px' }}>
                  Choose an item from the left sidebar to begin the review process.
                </div>
              </div>
            )}
          </div>

          {/* â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ RIGHT PANEL: Findings + Comments â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', maxHeight: 'calc(100vh - 160px)', overflowY: 'auto' }}>

            {/* Review Run Stats */}
            {reviewRun && (
              <div style={{
                background: 'rgba(255,255,255,0.04)',
                border: '1px solid rgba(255,255,255,0.08)',
                borderRadius: '16px',
                padding: '16px',
                animation: 'fadeIn 0.3s ease',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
                  <h3 style={{ margin: 0, fontSize: '13px', fontWeight: 700, color: '#8888cc', letterSpacing: '0.5px' }}>
                    REVIEW RUN RESULTS
                  </h3>
                  <span style={{
                    padding: '2px 8px', borderRadius: '20px', fontSize: '10px', fontWeight: 700,
                    background: reviewRun.run_status === 'COMPLETED' ? 'rgba(0,200,82,0.15)' : 'rgba(255,107,0,0.15)',
                    color: reviewRun.run_status === 'COMPLETED' ? '#00c852' : '#ff8c33',
                    border: `1px solid ${reviewRun.run_status === 'COMPLETED' ? 'rgba(0,200,82,0.3)' : 'rgba(255,107,0,0.3)'}`,
                  }}>
                    {reviewRun.run_status}
                  </span>
                </div>

                {/* Stat row */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px', marginBottom: '12px' }}>
                  {[
                    { label: 'Critical', count: counts.CRITICAL, color: '#ff4d4d' },
                    { label: 'High', count: counts.HIGH, color: '#ff8c33' },
                    { label: 'Medium', count: counts.MEDIUM, color: '#ffe033' },
                    { label: 'Low', count: counts.LOW, color: '#33d96a' },
                  ].map(s => (
                    <div key={s.label} style={{
                      background: `${s.color}15`,
                      border: `1px solid ${s.color}30`,
                      borderRadius: '8px', padding: '8px',
                      textAlign: 'center',
                    }}>
                      <div style={{ fontSize: '20px', fontWeight: 800, color: s.color }}>{s.count}</div>
                      <div style={{ fontSize: '10px', color: '#8888aa', fontWeight: 600 }}>{s.label}</div>
                    </div>
                  ))}
                </div>

                <div style={{ display: 'flex', gap: '16px', fontSize: '11px', color: '#8888aa' }}>
                  <span>ðŸ“‹ {reviewRun.rules_checked_count} rules checked</span>
                  <span>ðŸ“š {reviewRun.sources_consulted_count} sources consulted</span>
                </div>
                <div style={{ marginTop: '12px', fontSize: '11px', color: '#aaaacc' }}>
                  AI analysis: {reviewRun.ai_status || 'NOT_CONFIGURED'}
                  {reviewRun.ai_provider && ` · ${reviewRun.ai_provider}`}
                  {reviewRun.ai_model && ` / ${reviewRun.ai_model}`}
                  {reviewRun.ai_error_message && (
                    <p style={{ margin: '6px 0 0', color: '#ffb36b' }}>
                      {reviewRun.ai_error_message}
                    </p>
                  )}
                </div>
              </div>
            )}

            {/* Findings filter */}
            {reviewRun && allFindings.length > 0 && (
              <div style={{
                background: 'rgba(255,255,255,0.04)',
                border: '1px solid rgba(255,255,255,0.08)',
                borderRadius: '12px', padding: '12px',
                display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center',
              }}>
                <span style={{ fontSize: '11px', color: '#8888aa', fontWeight: 700 }}>FILTER:</span>
                {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map(s => {
                  const colors = s !== 'ALL' ? SEVERITY_COLORS[s] : null;
                  return (
                    <button
                      key={s}
                      onClick={() => setSeverityFilter(s)}
                      style={{
                        padding: '3px 10px', borderRadius: '20px', fontSize: '11px', fontWeight: 700,
                        border: `1px solid ${severityFilter === s ? (colors?.border || '#6464ff') : 'rgba(255,255,255,0.1)'}`,
                        background: severityFilter === s ? (colors?.bg || 'rgba(100,100,255,0.15)') : 'transparent',
                        color: severityFilter === s ? (colors?.text || '#9999ff') : '#8888aa',
                        cursor: 'pointer', transition: 'all 0.2s',
                      }}
                    >
                      {s}
                    </button>
                  );
                })}
                <button
                  onClick={() => setFindingTypeFilter(findingTypeFilter === 'DETERMINISTIC_RULE' ? 'ALL' : 'DETERMINISTIC_RULE')}
                  style={{
                    padding: '3px 10px', borderRadius: '20px', fontSize: '11px', fontWeight: 700,
                    border: `1px solid ${findingTypeFilter === 'DETERMINISTIC_RULE' ? '#9999ff' : 'rgba(255,255,255,0.1)'}`,
                    background: findingTypeFilter === 'DETERMINISTIC_RULE' ? 'rgba(100,100,255,0.15)' : 'transparent',
                    color: findingTypeFilter === 'DETERMINISTIC_RULE' ? '#9999ff' : '#8888aa',
                    cursor: 'pointer', transition: 'all 0.2s',
                  }}
                >
                  Rules only
                </button>
                <button
                  onClick={() => setFindingTypeFilter(findingTypeFilter === 'EVIDENCE_CLAIM' ? 'ALL' : 'EVIDENCE_CLAIM')}
                  style={{
                    padding: '3px 10px', borderRadius: '20px', fontSize: '11px', fontWeight: 700,
                    border: `1px solid ${findingTypeFilter === 'EVIDENCE_CLAIM' ? '#00c852' : 'rgba(255,255,255,0.1)'}`,
                    background: findingTypeFilter === 'EVIDENCE_CLAIM' ? 'rgba(0,200,82,0.1)' : 'transparent',
                    color: findingTypeFilter === 'EVIDENCE_CLAIM' ? '#00c852' : '#8888aa',
                    cursor: 'pointer', transition: 'all 0.2s',
                  }}
                >
                  Evidence only
                </button>
              </div>
            )}

            {/* Findings list */}
            {reviewRun && (
              <div>
                {filteredFindings.length === 0 ? (
                  <div style={{
                    textAlign: 'center', padding: '30px', color: '#6666aa',
                    background: 'rgba(0,200,82,0.05)', border: '1px dashed rgba(0,200,82,0.2)',
                    borderRadius: '12px',
                  }}>
                    <div style={{ fontSize: '28px', marginBottom: '8px' }}>âœ…</div>
                    <div style={{ fontWeight: 600, color: '#00c852' }}>No findings for this filter</div>
                    <div style={{ fontSize: '12px', marginTop: '4px' }}>All checks passed at this severity level.</div>
                  </div>
                ) : (
                  filteredFindings.map(finding => (
                    <FindingCard
                      key={finding.id}
                      finding={finding}
                      isActive={finding.id === activeFindingId}
                      onClick={setActiveFindingId}
                    />
                  ))
                )}
              </div>
            )}

            {/* Empty state â€” no review run yet */}
            {!reviewRun && selectedVersion && (
              <div style={{
                textAlign: 'center', padding: '40px 20px',
                background: 'rgba(255,255,255,0.02)', border: '1px dashed rgba(255,255,255,0.08)',
                borderRadius: '16px', color: '#6666aa',
              }}>
                <div style={{ fontSize: '36px', marginBottom: '10px' }}>ðŸ”¬</div>
                <div style={{ fontWeight: 600, fontSize: '14px', color: '#8888aa', marginBottom: '6px' }}>
                  No review yet
                </div>
                <div style={{ fontSize: '12px' }}>
                  Click "Run Governance Review" to trigger the rule engine and see findings here.
                </div>
              </div>
            )}

            {/* â”€â”€ Comment Thread â”€â”€ */}
            {selectedVersion && (
              <div style={{
                background: 'rgba(255,255,255,0.04)',
                border: '1px solid rgba(255,255,255,0.08)',
                borderRadius: '16px', padding: '16px',
              }}>
                <h3 style={{ margin: '0 0 12px', fontSize: '13px', fontWeight: 700, color: '#8888cc', letterSpacing: '0.5px' }}>
                  ðŸ’¬ REVIEW COMMENTS
                </h3>

                {comments.length === 0 && (
                  <p style={{ fontSize: '12px', color: '#6666aa', margin: '0 0 12px' }}>
                    No comments yet. Be the first to annotate.
                  </p>
                )}

                {comments.map(c => (
                  <div key={c.id} style={{
                    padding: '10px', marginBottom: '8px',
                    background: 'rgba(0,0,0,0.2)', borderRadius: '8px',
                    borderLeft: '3px solid rgba(100,100,255,0.4)',
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                      <span style={{ fontSize: '11px', fontWeight: 700, color: '#9999ff' }}>
                        {c.author_username}
                      </span>
                      <span style={{ fontSize: '10px', color: '#6666aa' }}>
                        {new Date(c.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    {c.finding && (
                      <span style={{
                        fontSize: '10px', color: '#ffd700', background: '#ffd70015',
                        padding: '1px 6px', borderRadius: '10px', marginBottom: '4px', display: 'inline-block',
                      }}>
                        re: finding
                      </span>
                    )}
                    <p style={{ margin: '4px 0 0', fontSize: '12px', color: '#c8c8e0', lineHeight: '1.5' }}>
                      {c.comment_text}
                    </p>
                  </div>
                ))}

                {/* Comment form */}
                {reviewRun && allFindings.length > 0 && (
                  <select
                    value={commentFindingId}
                    onChange={e => setCommentFindingId(e.target.value)}
                    id="select-comment-finding"
                    style={{
                      width: '100%', background: 'rgba(0,0,0,0.3)',
                      border: '1px solid rgba(255,255,255,0.1)', borderRadius: '6px',
                      color: '#e8e8f8', padding: '7px', fontSize: '12px',
                      marginBottom: '8px', boxSizing: 'border-box',
                    }}
                  >
                    <option value="">General comment (no specific finding)</option>
                    {allFindings.map(f => (
                      <option key={f.id} value={f.id}>
                        [{f.severity}] {f.category} â€” "{f.flagged_text.slice(0, 40)}..."
                      </option>
                    ))}
                  </select>
                )}

                <div style={{ display: 'flex', gap: '8px' }}>
                  <input
                    value={commentText}
                    onChange={e => setCommentText(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && handleCommentSubmit()}
                    placeholder="Add a comment..."
                    id="input-comment-text"
                    style={{
                      flex: 1, background: 'rgba(0,0,0,0.3)',
                      border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px',
                      color: '#e8e8f8', padding: '9px 12px', fontSize: '12px',
                      fontFamily: 'inherit',
                    }}
                  />
                  <button
                    onClick={handleCommentSubmit}
                    disabled={!commentText.trim()}
                    id="btn-submit-comment"
                    style={{
                      padding: '9px 14px', borderRadius: '8px', border: 'none',
                      background: commentText.trim()
                        ? 'linear-gradient(135deg, #4040cc, #6464ff)'
                        : 'rgba(255,255,255,0.08)',
                      color: commentText.trim() ? '#fff' : '#6666aa',
                      fontWeight: 700, fontSize: '13px',
                      cursor: commentText.trim() ? 'pointer' : 'not-allowed',
                    }}
                  >
                    Post
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
