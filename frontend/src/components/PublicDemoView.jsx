import React, { useMemo, useState } from 'react';
import {
  ArrowDown, ArrowRight, ArrowUpRight, BadgeCheck, BookOpen, Check,
  CheckCircle2, ChevronDown, CircleAlert, ClipboardCheck, Clock3, FileCheck2,
  FileClock, FileSearch, Fingerprint, Flag, Gauge, Layers3, LockKeyhole,
  Menu, MessageSquareText, ScanSearch, Shield, ShieldAlert, ShieldCheck,
  Sparkles, X,
} from 'lucide-react';
import '../App.css';

const metrics = [
  { label: 'Brand rules', value: '24', note: 'Across 3 sample brands', icon: ShieldCheck, color: 'violet' },
  { label: 'Claims reviewed', value: '186', note: 'Illustrative review volume', icon: FileCheck2, color: 'cyan' },
  { label: 'Sample findings', value: '07', note: 'Across demo content', icon: Flag, color: 'amber' },
  { label: 'Governance score', value: '94%', note: 'Illustrative score only', icon: Gauge, color: 'green' },
];

const findings = [
  { id: 1, title: 'Spring launch email', brand: 'EcoVolt', finding: 'Unsupported savings claim', category: 'Unsupported claims', severity: 'High', status: 'Needs Review' },
  { id: 2, title: 'Everyday essentials', brand: 'PureNest', finding: 'Prohibited phrase detected', category: 'Prohibited phrases', severity: 'Critical', status: 'Rejected' },
  { id: 3, title: 'Investor update', brand: 'FinEdge', finding: 'Risk disclaimer missing', category: 'Missing disclaimers', severity: 'Medium', status: 'Needs Review' },
  { id: 4, title: 'New home collection', brand: 'PureNest', finding: 'Voice consistency check', category: 'Brand voice inconsistency', severity: 'Low', status: 'Passed' },
  { id: 5, title: 'Clean energy guide', brand: 'EcoVolt', finding: 'Evidence source not linked', category: 'Unverified evidence', severity: 'High', status: 'Needs Review' },
  { id: 6, title: 'Planning with confidence', brand: 'FinEdge', finding: 'Performance claim needs review', category: 'Unsupported claims', severity: 'Medium', status: 'Passed' },
  { id: 7, title: 'Product detail page', brand: 'PureNest', finding: 'Required qualifier missing', category: 'Missing disclaimers', severity: 'Low', status: 'Passed' },
];

const categories = [
  { label: 'Unsupported claims', count: '02', icon: FileSearch, color: 'rose' },
  { label: 'Prohibited phrases', count: '01', icon: ShieldAlert, color: 'amber' },
  { label: 'Missing disclaimers', count: '02', icon: ClipboardCheck, color: 'violet' },
  { label: 'Brand voice inconsistency', count: '01', icon: MessageSquareText, color: 'cyan' },
  { label: 'Unverified evidence', count: '01', icon: Fingerprint, color: 'blue' },
];

const features = [
  { icon: BookOpen, title: 'Brand knowledge management', copy: 'Keep approved claims, voice guidance, source documents, and brand rules organized in one workspace.' },
  { icon: ScanSearch, title: 'Content governance', copy: 'Review copy against the right brand standards before it reaches customers or channels.' },
  { icon: BadgeCheck, title: 'Evidence-based claim verification', copy: 'Connect marketing claims to approved source material and make evidence gaps visible.' },
  { icon: ShieldAlert, title: 'AI-assisted risk detection', copy: 'Surface potential risk areas with explainable checks and reviewer-friendly context.' },
  { icon: ClipboardCheck, title: 'Review and approval workflow', copy: 'Coordinate creator and reviewer handoffs with clear states and accountable decisions.' },
  { icon: FileClock, title: 'Version history', copy: 'Keep revisions distinct so teams can understand what changed and what was reviewed.' },
  { icon: Fingerprint, title: 'Audit trail', copy: 'Preserve a transparent timeline of decisions, status changes, and review events.' },
  { icon: Layers3, title: 'Multi-workspace management', copy: "Separate client workspaces and apply role-based access to each organization's content." },
];

const stages = ['Submitted', 'Under Review', 'Changes Requested', 'Approved', 'Rejected'];
const initialWorkflow = [
  { title: 'Spring launch email', brand: 'EcoVolt', status: 'Under Review', role: 'Brand reviewer' },
  { title: 'Product detail page', brand: 'PureNest', status: 'Changes Requested', role: 'Content creator' },
  { title: 'Investor update', brand: 'FinEdge', status: 'Approved', role: 'Brand reviewer' },
];

const history = [
  { version: 'v 03', change: 'Added verified source citation', time: 'Today · 10:42 AM', status: 'Under review', role: 'Brand reviewer', event: 'Evidence attached' },
  { version: 'v 02', change: 'Revised savings statement', time: 'Yesterday · 4:18 PM', status: 'Changes requested', role: 'Account manager', event: 'Revision requested' },
  { version: 'v 01', change: 'Initial content submitted', time: 'Oct 21 · 9:06 AM', status: 'Submitted', role: 'Content creator', event: 'Review created' },
];

const sampleClaims = [
  { brand: 'EcoVolt', claim: 'Our product reduces energy consumption by 80%.', source: 'DEMO · Source record EV-014 (illustrative)', status: 'Evidence missing', risk: 'High', explanation: 'No linked evidence in this illustrative record supports the quantified savings statement.', correction: 'Provide a verifiable source for the figure or revise the claim to remove the unsupported percentage.' },
  { brand: 'PureNest', claim: 'A gentler choice for everyday home care.', source: 'DEMO · Brand voice guide PN-003 (illustrative)', status: 'Needs reviewer confirmation', risk: 'Low', explanation: 'The sample wording aligns with the example voice guidance, but this record is not a real verification.', correction: 'Confirm the wording against current approved brand guidance before publication.' },
];

const riskTone = {
  Critical: 'critical',
  High: 'high',
  Medium: 'medium',
  Low: 'low',
};

function Badge({ children, tone = 'neutral' }) {
  return <span className={`demo-badge demo-badge--${tone}`}>{children}</span>;
}

function SectionHeading({ eyebrow, title, copy, id }) {
  return (
    <div className="demo-section-heading" id={id}>
      <p className="demo-eyebrow">{eyebrow}</p>
      <h2>{title}</h2>
      {copy && <p className="demo-section-copy">{copy}</p>}
    </div>
  );
}

function simulateAnalysis(content, brand) {
  const checks = [];
  if (/\b(100%|guaranteed|guarantees|always|never)\b/i.test(content)) {
    checks.push({ category: 'Unsupported claims', severity: 'High', detail: 'Absolute or guaranteed language may need substantiation and careful review.', suggestion: 'Qualify the statement and link approved evidence for any measurable outcome.' });
  }
  if (/\b(risk[- ]free|miracle|world['’]?s best|cure)\b/i.test(content)) {
    checks.push({ category: 'Prohibited phrases', severity: 'Critical', detail: 'A phrase in this sample matches a simulated prohibited-language rule.', suggestion: 'Replace absolute or prohibited wording with a specific, supportable description.' });
  }
  if (/\b(?:80%|save[sd]?\s+\d+%|reduce[sd]?\s+\d+%)(?!\w)/i.test(content)) {
    checks.push({ category: 'Unverified evidence', severity: 'High', detail: 'A quantified performance claim should be connected to an approved evidence source.', suggestion: 'Attach a current, verifiable source or remove the unsupported figure.' });
  }
  if (brand === 'FinEdge' && !/\b(risk|investment|capital)\b/i.test(content)) {
    checks.push({ category: 'Missing disclaimers', severity: 'Medium', detail: 'Financial content may require a contextual risk disclaimer in this demo scenario.', suggestion: 'Ask a qualified reviewer to confirm required disclosures for the intended audience.' });
  }
  if (content.length > 35 && !/\b(we|our|you|your)\b/i.test(content)) {
    checks.push({ category: 'Brand voice inconsistency', severity: 'Low', detail: 'The sample copy may not use the selected brand’s conversational voice.', suggestion: 'Use direct, audience-focused language and compare it with approved brand guidance.' });
  }
  return checks;
}

function DemoAnalysis() {
  const [brand, setBrand] = useState('EcoVolt');
  const [content, setContent] = useState('');
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const analyze = (event) => {
    event.preventDefault();
    const text = content.trim();
    if (!text) {
      setError('Enter sample marketing copy to analyze.');
      setResult(null);
      return;
    }
    if (text.length > 2000) {
      setError('Keep the sample under 2,000 characters.');
      setResult(null);
      return;
    }
    setError('');
    setResult({ checks: simulateAnalysis(text, brand), content: text });
  };

  return (
    <section className="demo-section" id="checker">
      <SectionHeading eyebrow="Try the simulation" title="A practical content check" copy="Enter sample marketing copy to see a local, rule-based demonstration. Nothing is sent to an API or saved." />
      <div className="demo-checker-grid">
        <form className="demo-card demo-checker-form" onSubmit={analyze}>
          <div className="demo-card-heading">
            <div><span className="demo-icon-wrap demo-icon-wrap--violet"><Sparkles size={18} /></span></div>
            <div><h3>Sample content checker</h3><p>Simulated public demonstration · not a real AI analysis</p></div>
          </div>
          <label className="demo-field-label" htmlFor="demo-brand">Demonstration brand</label>
          <div className="demo-select-wrap">
            <select id="demo-brand" value={brand} onChange={(event) => setBrand(event.target.value)}>
              <option>EcoVolt</option><option>PureNest</option><option>FinEdge</option>
            </select>
            <ChevronDown size={16} aria-hidden="true" />
          </div>
          <label className="demo-field-label" htmlFor="demo-content">Sample marketing copy</label>
          <textarea
            id="demo-content"
            maxLength={2000}
            rows={5}
            placeholder="Try: Our solution reduces energy consumption by 80% — guaranteed."
            value={content}
            onChange={(event) => setContent(event.target.value)}
          />
          <div className="demo-form-foot">
            <span>{content.length}/2,000 characters</span>
            <button type="submit" className="demo-button demo-button--primary">Analyze content <ArrowRight size={16} /></button>
          </div>
          {error && <p className="demo-error" role="alert">{error}</p>}
        </form>

        <div className="demo-card demo-analysis-result" aria-live="polite">
          {!result ? (
            <div className="demo-empty-analysis">
              <span className="demo-empty-icon"><ScanSearch size={24} /></span>
              <h3>Your sample review appears here</h3>
              <p>Run a check to see simulated risk categories, severity, and suggested improvements.</p>
              <div className="demo-sim-note"><LockKeyhole size={15} /> Local demo only · no personal or workspace data</div>
            </div>
          ) : (
            <>
              <div className="demo-card-heading">
                <div><span className="demo-icon-wrap demo-icon-wrap--cyan"><ScanSearch size={18} /></span></div>
                <div><h3>Simulation result</h3><p>{brand} · illustrative checks only</p></div>
                <Badge tone={result.checks.length ? 'warning' : 'success'}>{result.checks.length ? `${result.checks.length} finding${result.checks.length > 1 ? 's' : ''}` : 'No sample flags'}</Badge>
              </div>
              <div className="demo-analyzed-copy">“{result.content}”</div>
              {result.checks.length ? (
                <div className="demo-check-results">
                  {result.checks.map((check) => (
                    <article className="demo-check-result" key={`${check.category}-${check.severity}`}>
                      <div className="demo-check-result-top"><strong>{check.category}</strong><Badge tone={riskTone[check.severity]}>{check.severity}</Badge></div>
                      <p>{check.detail}</p>
                      <div className="demo-suggestion"><CheckCircle2 size={15} /><span>{check.suggestion}</span></div>
                    </article>
                  ))}
                </div>
              ) : (
                <div className="demo-clear-state"><CheckCircle2 size={18} /><div><strong>No sample flags detected</strong><p>That is not a real compliance approval. Always follow your organization’s review process.</p></div></div>
              )}
              <div className="demo-governance-result"><span>Sample governance result</span><strong>{result.checks.some((check) => ['Critical', 'High'].includes(check.severity)) ? 'Reviewer attention recommended' : result.checks.length ? 'Review suggested' : 'No simulated risk detected'}</strong></div>
            </>
          )}
        </div>
      </div>
    </section>
  );
}

export default function PublicDemoView() {
  const [severityFilter, setSeverityFilter] = useState('All');
  const [statusFilter, setStatusFilter] = useState('All');
  const [activeClaim, setActiveClaim] = useState(0);
  const [workflow, setWorkflow] = useState(initialWorkflow);
  const [menuOpen, setMenuOpen] = useState(false);

  const filteredFindings = useMemo(() => findings.filter((item) =>
    (severityFilter === 'All' || item.severity === severityFilter)
    && (statusFilter === 'All' || item.status === statusFilter)
  ), [severityFilter, statusFilter]);

  const cycleWorkflow = (index) => {
    setWorkflow((items) => items.map((item, current) => {
      if (current !== index) return item;
      const currentIndex = stages.indexOf(item.status);
      return { ...item, status: stages[(currentIndex + 1) % stages.length] };
    }));
  };

  return (
    <div className="public-demo">
      <header className="demo-nav">
        <div className="demo-shell demo-nav-inner">
          <a className="demo-brand" href="#home" aria-label="Inkloom Guardian home">
            <span className="demo-brand-mark"><ShieldCheck size={21} /></span>
            <span><strong>Inkloom Guardian</strong><small>Brand governance, made clear.</small></span>
          </a>
          <button className="demo-menu-toggle" type="button" aria-label={menuOpen ? 'Close navigation' : 'Open navigation'} aria-expanded={menuOpen} onClick={() => setMenuOpen(!menuOpen)}>
            {menuOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
          <nav className={`demo-nav-links ${menuOpen ? 'is-open' : ''}`} aria-label="Main navigation">
            <a href="#overview" onClick={() => setMenuOpen(false)}>Overview</a>
            <a href="#features" onClick={() => setMenuOpen(false)}>Features</a>
            <a href="#how-it-works" onClick={() => setMenuOpen(false)}>How it works</a>
            <a href="#security" onClick={() => setMenuOpen(false)}>Security</a>
            <a className="demo-nav-demo" href="#demo-dashboard" onClick={() => setMenuOpen(false)}><span className="demo-live-dot" /> Public demo</a>
          </nav>
        </div>
      </header>

      <main>
        <section className="demo-hero" id="home">
          <div className="demo-shell demo-hero-grid">
            <div className="demo-hero-copy">
              <div className="demo-overline"><span className="demo-live-dot" /> PUBLIC DEMONSTRATION · SAMPLE DATA</div>
              <h1>Protect Your Brand.<br /><span>Build Content People Can Trust.</span></h1>
              <p>Inkloom Guardian helps organizations enforce brand standards, verify claims, detect content risks, and manage evidence-based approval workflows in one intelligent platform.</p>
              <div className="demo-hero-actions">
                <a className="demo-button demo-button--primary" href="#demo-dashboard">Explore Live Demo <ArrowRight size={17} /></a>
                <a className="demo-button demo-button--quiet" href="#how-it-works">Discover How It Works <ArrowDown size={16} /></a>
              </div>
              <div className="demo-hero-assurance"><LockKeyhole size={15} /><span>No account needed</span><i /> <span>Private workspaces stay protected</span></div>
            </div>
            <div className="demo-hero-visual" aria-label="Illustrative governance dashboard preview">
              <div className="demo-preview-card">
                <div className="demo-preview-head"><div><span className="demo-preview-kicker">DEMO WORKSPACE</span><h2>Governance overview</h2></div><span className="demo-preview-status"><span className="demo-live-dot" /> Sample</span></div>
                <div className="demo-preview-score"><div className="demo-score-ring"><strong>94</strong><small>/ 100</small></div><div><span>Illustrative score</span><strong>Strong governance</strong><small>Sample demonstration data</small></div></div>
                <div className="demo-preview-bars">
                  <div><span><i className="demo-bar-dot demo-bar-dot--violet" /> Claims with evidence</span><strong>82%</strong><b><i style={{ width: '82%' }} /></b></div>
                  <div><span><i className="demo-bar-dot demo-bar-dot--cyan" /> Reviews completed</span><strong>76%</strong><b><i style={{ width: '76%' }} /></b></div>
                  <div><span><i className="demo-bar-dot demo-bar-dot--amber" /> Items for attention</span><strong>07</strong><b><i style={{ width: '34%' }} /></b></div>
                </div>
                <div className="demo-preview-foot"><Shield size={15} /><span>Illustrative records only. Not connected to customer data.</span></div>
              </div>
              <div className="demo-floating-note"><span className="demo-floating-check"><Check size={15} /></span><span><strong>Evidence-linked review</strong><small>Transparent by design</small></span></div>
            </div>
          </div>
        </section>

        <section className="demo-shell demo-metrics-section" id="overview">
          <div className="demo-metrics-label"><span>PRODUCT AT A GLANCE</span><Badge tone="demo">Sample demonstration data</Badge></div>
          <div className="demo-metrics">
            {metrics.map((metric) => {
              const Icon = metric.icon;
              return <article className="demo-metric-card" key={metric.label}><span className={`demo-metric-icon demo-metric-icon--${metric.color}`}><Icon size={18} /></span><span className="demo-metric-label">{metric.label}</span><strong>{metric.value}</strong><small>{metric.note}</small></article>;
            })}
          </div>
        </section>

        <section className="demo-section demo-shell" id="features">
          <SectionHeading eyebrow="ONE GOVERNANCE WORKFLOW" title="Clarity from brief to approval" copy="Bring standards, evidence, and human decisions together, without losing the context behind each review." />
          <div className="demo-feature-grid">
            {features.map((feature, index) => {
              const Icon = feature.icon;
              return <article className="demo-feature-card" key={feature.title}><span className="demo-feature-number">0{index + 1}</span><span className="demo-feature-icon"><Icon size={19} /></span><h3>{feature.title}</h3><p>{feature.copy}</p></article>;
            })}
          </div>
        </section>

        <section className="demo-section demo-shell" id="demo-dashboard">
          <SectionHeading eyebrow="PUBLIC DEMO DASHBOARD" title="Explore the governance workspace" copy="Every name, metric, and activity below is illustrative sample data—not live company performance or customer records." />
          <div className="demo-dashboard">
            <div className="demo-dashboard-top">
              <div><div className="demo-dashboard-title"><span className="demo-dashboard-mark"><ShieldCheck size={18} /></span><div><h3>Governance overview</h3><p>Illustrative workspace · 3 sample brands</p></div></div></div>
              <Badge tone="demo">DEMO DATA</Badge>
            </div>
            <div className="demo-dashboard-metrics">{metrics.map((metric) => <div key={metric.label}><span>{metric.label}</span><strong>{metric.value}</strong><small>{metric.note}</small></div>)}</div>
            <div className="demo-findings-head">
              <div><h3>Sample content activity</h3><p>Review queue · all records marked as demo</p></div>
              <div className="demo-filter-group">
                <label htmlFor="severity-filter">Severity</label>
                <select id="severity-filter" value={severityFilter} onChange={(event) => setSeverityFilter(event.target.value)}>{['All', 'Critical', 'High', 'Medium', 'Low'].map((value) => <option key={value}>{value}</option>)}</select>
                <label htmlFor="status-filter">Status</label>
                <select id="status-filter" value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>{['All', 'Passed', 'Needs Review', 'Rejected'].map((value) => <option key={value}>{value}</option>)}</select>
              </div>
            </div>
            <div className="demo-table-wrap">
              <table className="demo-activity-table">
                <thead><tr><th>Content</th><th>Brand</th><th>Finding</th><th>Severity</th><th>Status</th><th>Record</th></tr></thead>
                <tbody>{filteredFindings.map((item) => <tr key={item.id}><td><strong>{item.title}</strong><small>Sample review #{String(item.id).padStart(3, '0')}</small></td><td>{item.brand}</td><td><span className="demo-finding-label">{item.finding}</span><small>{item.category}</small></td><td><Badge tone={riskTone[item.severity]}>{item.severity}</Badge></td><td><Badge tone={item.status === 'Passed' ? 'success' : item.status === 'Rejected' ? 'critical' : 'warning'}>{item.status}</Badge></td><td><Badge tone="demo">DEMO</Badge></td></tr>)}</tbody>
              </table>
              {!filteredFindings.length && <div className="demo-no-results"><CircleAlert size={17} /> No sample findings match these filters.</div>}
            </div>
            <div className="demo-risk-footer"><span><Shield size={15} /> Sample risk categories</span><div>{categories.map((category) => <span className="demo-risk-chip" key={category.label}><i className={`demo-risk-dot demo-risk-dot--${category.color}`} />{category.label}</span>)}</div></div>
          </div>
        </section>

        <DemoAnalysis />

        <section className="demo-section demo-shell" id="claims">
          <SectionHeading eyebrow="CLAIM VERIFICATION · DEMO" title="Show the evidence behind every claim" copy="Sample claim records make gaps visible. No certification, study, or regulatory approval is implied." />
          <div className="demo-claim-layout">
            <div className="demo-claim-list" role="tablist" aria-label="Sample claims">
              {sampleClaims.map((claim, index) => <button className={`demo-claim-tab ${activeClaim === index ? 'is-active' : ''}`} role="tab" aria-selected={activeClaim === index} key={claim.brand} onClick={() => setActiveClaim(index)}><span><small>{claim.brand} · DEMO</small><strong>{claim.claim}</strong></span><ArrowUpRight size={16} /></button>)}
            </div>
            <article className="demo-card demo-claim-detail">
              <div className="demo-claim-detail-head"><span className="demo-icon-wrap demo-icon-wrap--amber"><FileSearch size={18} /></span><div><span className="demo-small-label">SAMPLE EVIDENCE REVIEW</span><h3>{sampleClaims[activeClaim].brand} claim check</h3></div><Badge tone={riskTone[sampleClaims[activeClaim].risk]}>{sampleClaims[activeClaim].risk} risk</Badge></div>
              <blockquote>“{sampleClaims[activeClaim].claim}”</blockquote>
              <div className="demo-claim-facts"><div><span>Evidence source</span><strong>{sampleClaims[activeClaim].source}</strong></div><div><span>Verification status</span><strong>{sampleClaims[activeClaim].status}</strong></div><div><span>Explanation</span><p>{sampleClaims[activeClaim].explanation}</p></div><div className="demo-claim-recommendation"><span>Suggested correction</span><p>{sampleClaims[activeClaim].correction}</p></div></div>
            </article>
          </div>
        </section>

        <section className="demo-section demo-shell" id="how-it-works">
          <SectionHeading eyebrow="HUMAN-CENTERED GOVERNANCE" title="A clear path from submission to audit" copy="The sample workflow is interactive. Change a record’s state to explore the review lifecycle—your changes stay in this browser session." />
          <div className="demo-workflow-steps">{['Submit content', 'Governance scan', 'Reviewer assessment', 'Approve or revise', 'Audit record'].map((step, index) => <div className="demo-workflow-step" key={step}><span>{index < 3 ? <CheckCircle2 size={17} /> : <span>{index + 1}</span>}</span><strong>{step}</strong>{index < 4 && <i />}</div>)}</div>
          <div className="demo-workflow-grid">
            {workflow.map((item, index) => <article className="demo-workflow-card" key={item.title}><div className="demo-workflow-card-head"><span><span className="demo-live-dot" /> DEMO RECORD</span><button type="button" onClick={() => cycleWorkflow(index)} aria-label={`Advance status for ${item.title}`}>Change status <ArrowRight size={14} /></button></div><h3>{item.title}</h3><p>{item.brand} · Sample content review</p><div className="demo-workflow-status"><span>Current status</span><Badge tone={item.status === 'Approved' ? 'success' : item.status === 'Rejected' ? 'critical' : 'warning'}>{item.status}</Badge></div><div className="demo-workflow-meta"><span>Responsible role</span><strong>{item.role}</strong></div></article>)}
          </div>
        </section>

        <section className="demo-section demo-shell">
          <SectionHeading eyebrow="TRACEABLE CHANGES · DEMO" title="Keep every decision in context" copy="An illustrative version history connects content changes to review events and reviewer roles." />
          <div className="demo-history-card">
            <div className="demo-history-top"><div><h3>Spring launch email</h3><p>EcoVolt · illustrative version history</p></div><Badge tone="demo">DEMO TIMELINE</Badge></div>
            <div className="demo-timeline">{history.map((item, index) => <article className="demo-timeline-item" key={item.version}><span className={`demo-timeline-marker ${index === 0 ? 'is-current' : ''}`}>{index === 0 ? <Clock3 size={14} /> : <Check size={14} />}</span><div className="demo-timeline-version"><strong>{item.version}</strong><small>{item.time}</small></div><div className="demo-timeline-change"><strong>{item.change}</strong><small>Reviewer role: {item.role}</small></div><Badge tone={item.status === 'Submitted' ? 'neutral' : 'warning'}>{item.status}</Badge><div className="demo-timeline-event"><span>Audit event</span><strong>{item.event}</strong></div></article>)}</div>
          </div>
        </section>

        <section className="demo-section demo-shell" id="security">
          <div className="demo-security-panel">
            <div className="demo-security-icon"><LockKeyhole size={22} /></div>
            <div className="demo-security-copy"><p className="demo-eyebrow">SECURITY & TRUST</p><h2>Public exploration. Private by design.</h2><p>This demonstration runs on local illustrative data and does not request personal information, create accounts, or call private workspace APIs. Authenticated workspace operations remain protected by server-side authentication, role checks, and tenant-scoped permissions.</p></div>
            <div className="demo-security-points"><span><CheckCircle2 size={16} /> No public workspace data</span><span><CheckCircle2 size={16} /> No demo credentials or token exposure</span><span><CheckCircle2 size={16} /> Private API permissions unchanged</span></div>
          </div>
        </section>
      </main>

      <footer className="demo-footer"><div className="demo-shell demo-footer-inner"><a className="demo-brand" href="#home"><span className="demo-brand-mark"><ShieldCheck size={19} /></span><span><strong>Inkloom Guardian</strong><small>Protect what your brand stands for.</small></span></a><span>© 2026 Inkloom Guardian · Public demonstration</span><a href="#home">Back to top <ArrowUpRight size={14} /></a></div><div className="demo-shell demo-footer-note">All brands, records, metrics, and workflow activity shown here are illustrative sample data created for this public demonstration.</div></footer>
    </div>
  );
}
