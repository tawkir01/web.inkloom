"""
rule_engine.py — Deterministic Brand Governance Rule Engine
============================================================

This module is the heart of Inkloom Guardian's automated review system.

HOW IT WORKS (beginner-friendly explanation):
----------------------------------------------
Think of this file as a very meticulous editor who reads through submitted
marketing copy and cross-checks every sentence against three sources of truth:

1. BRAND RULES: A list of forbidden phrases and required terms defined by the
   marketing team (e.g., "Never say 'guaranteed' without qualifiers").

2. APPROVED CLAIMS: Exact statements that the legal team has vetted and approved
   (e.g., "EcoVolt batteries last up to 40% longer in cold climates").

3. SOURCE DOCUMENTS: Scientific studies, trial reports, and legal filings
   stored in the database as versioned passages.

For every rule that matches, the engine creates a "Finding" — a structured
record that identifies:
  - The EXACT problematic text (character position start → end)
  - WHY it was flagged (explanation)
  - WHAT evidence supports or contradicts the claim
  - HOW SEVERE the issue is (LOW / MEDIUM / HIGH / CRITICAL)

All citations link to real database records — no hallucinated references.
"""

import re
import logging
from typing import Any
from dataclasses import dataclass, field
from governance.models import BrandRule, ApprovedClaim, SourceDocumentVersion

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class RawFinding:
    """
    An intermediate result object produced by the rule engine before being
    persisted to the database as a Finding model instance.

    Think of it like a sticky note the editor attaches to the text.
    """
    finding_type: str         # 'DETERMINISTIC_RULE' or 'EVIDENCE_CLAIM'
    category: str             # Human-readable category label
    flagged_text: str         # The exact problematic phrase
    start_char: int           # Where in the text the issue starts (0-indexed)
    end_char: int             # Where it ends
    severity: str             # LOW / MEDIUM / HIGH / CRITICAL
    verification_status: str  # SUPPORTED / CONTRADICTED / UNSUPPORTED / UNABLE_TO_DETERMINE
    explanation: str          # Why this was flagged
    quoted_passage: str = ''  # The exact source evidence passage (if any)
    brand_rule_id: Any = None  # UUID of the BrandRule that triggered this (if any)
    approved_claim_id: Any = None  # UUID of the related ApprovedClaim (if any)
    source_version_id: Any = None  # UUID of the SourceDocumentVersion cited (if any)
    suggested_correction: str = ''  # Suggested replacement copy
    confidence: float = 1.0       # How confident is this finding (0.0 – 1.0)
    is_citation_validated: bool = False  # True = evidence verified against real DB record


@dataclass
class EngineResult:
    """
    The final output package from the rule engine for one ContentVersion.
    Contains all raw findings plus metadata about the run.
    """
    findings: list = field(default_factory=list)
    rules_checked_count: int = 0
    sources_consulted_count: int = 0
    error_message: str = ''


# ---------------------------------------------------------------------------
# Helper: Find all occurrences of a phrase in text (case-insensitive)
# ---------------------------------------------------------------------------

def _find_all_spans(text: str, phrase: str) -> list[tuple[int, int]]:
    """
    Returns a list of (start_char, end_char) for every occurrence of `phrase`
    inside `text`, using case-insensitive whole-word matching.

    Example:
        text = "Do not use Guaranteed results"
        phrase = "guaranteed"
        → [(11, 21)]   ← positions 11 to 21 in the string
    """
    spans = []
    # We use \\b word-boundary anchors so we don't match "guarantee" inside "guaranteed"
    try:
        pattern = re.compile(r'\b' + re.escape(phrase) + r'\b', re.IGNORECASE)
        for match in pattern.finditer(text):
            spans.append((match.start(), match.end()))
    except re.error:
        # If the phrase itself contains invalid regex characters, fall back to exact search
        lower_text = text.lower()
        lower_phrase = phrase.lower()
        start = 0
        while True:
            idx = lower_text.find(lower_phrase, start)
            if idx == -1:
                break
            spans.append((idx, idx + len(lower_phrase)))
            start = idx + 1
    return spans


def _text_contains(text: str, phrase: str) -> bool:
    """
    Returns True if `phrase` appears in `text` (case-insensitive, word-boundary aware).
    """
    return len(_find_all_spans(text, phrase)) > 0


# ---------------------------------------------------------------------------
# STEP 1: Deterministic Brand Rule Checks
# ---------------------------------------------------------------------------

def run_brand_rule_checks(text: str, workspace) -> tuple[list[RawFinding], int]:
    """
    Checks submitted copy against all active BrandRule records for this workspace.

    Returns:
        - List of RawFinding objects for every violation found
        - Count of rules checked

    RULE TYPES HANDLED:
      - PROHIBITED_PHRASE: Flag any occurrence of the pattern_or_phrase
      - DISALLOWED_CLAIM: Flag any wording matching the pattern
      - REQUIRED_TERM: Flag if the required phrase is ABSENT from the text
      - REQUIRED_QUALIFIER: Flag if the qualifier phrase is absent
      - TONE_GUIDANCE: Flag if problematic tone words appear (advisory findings)
    """
    findings = []
    active_rules = BrandRule.objects.filter(workspace=workspace, is_active=True)
    rules_checked = active_rules.count()

    for rule in active_rules:
        phrase = rule.pattern_or_phrase.strip()
        if not phrase:
            continue

        if rule.rule_type in (
            BrandRule.RuleType.PROHIBITED_PHRASE,
            BrandRule.RuleType.DISALLOWED_CLAIM,
        ):
            # Find every occurrence of this forbidden phrase
            spans = _find_all_spans(text, phrase)
            for start, end in spans:
                flagged = text[start:end]
                correction = rule.preferred_alternative or f"Remove or replace '{phrase}'"
                findings.append(RawFinding(
                    finding_type='DETERMINISTIC_RULE',
                    category=f"Brand Rule: {rule.get_rule_type_display()}",
                    flagged_text=flagged,
                    start_char=start,
                    end_char=end,
                    severity=rule.severity,
                    verification_status='CONTRADICTED',  # Violates brand policy
                    explanation=rule.explanation,
                    suggested_correction=correction,
                    brand_rule_id=rule.id,
                    confidence=1.0,
                    is_citation_validated=True,  # Based on stored BrandRule, not hallucinated
                ))

        elif rule.rule_type in (
            BrandRule.RuleType.REQUIRED_TERM,
            BrandRule.RuleType.REQUIRED_QUALIFIER,
        ):
            # Check if the REQUIRED phrase is missing from the text
            if not _text_contains(text, phrase):
                findings.append(RawFinding(
                    finding_type='DETERMINISTIC_RULE',
                    category=f"Brand Rule: {rule.get_rule_type_display()}",
                    flagged_text='[Entire submission — missing required term]',
                    start_char=0,
                    end_char=len(text),
                    severity=rule.severity,
                    verification_status='UNSUPPORTED',  # Missing required element
                    explanation=rule.explanation,
                    suggested_correction=rule.preferred_alternative or f"Add required term: '{phrase}'",
                    brand_rule_id=rule.id,
                    confidence=1.0,
                    is_citation_validated=True,
                ))

        elif rule.rule_type == BrandRule.RuleType.TONE_GUIDANCE:
            # Tone findings are advisory — flag if problematic tone words are present
            spans = _find_all_spans(text, phrase)
            for start, end in spans:
                findings.append(RawFinding(
                    finding_type='DETERMINISTIC_RULE',
                    category='Brand Rule: Tone Guidance',
                    flagged_text=text[start:end],
                    start_char=start,
                    end_char=end,
                    severity='LOW',  # Tone guidance is advisory, always LOW
                    verification_status='UNABLE_TO_DETERMINE',
                    explanation=rule.explanation,
                    suggested_correction=rule.preferred_alternative or 'Consider rephrasing for brand tone.',
                    brand_rule_id=rule.id,
                    confidence=0.8,
                    is_citation_validated=True,
                ))

    return findings, rules_checked


# ---------------------------------------------------------------------------
# STEP 2: Evidence & Claim Verification
# ---------------------------------------------------------------------------

def run_claim_verification(text: str, workspace) -> tuple[list[RawFinding], int]:
    """
    Verifies factual and legal claims in submitted copy against:
      a) ApprovedClaim records (permitted statements + disallowed variations)
      b) SourceDocumentVersion passages (evidentiary source records)

    HOW IT WORKS:
      1. Load all active ApprovedClaims for this workspace.
      2. Check if any DISALLOWED variation of a claim appears in the text → flag it.
      3. Check if an approved claim's REQUIRED QUALIFIER is missing → flag it.
      4. Fetch all valid SourceDocumentVersions for this workspace and search
         their passage_excerpts for any sentences that contradict what's in the text.

    Returns:
        - List of RawFinding objects for every claim issue
        - Count of source versions consulted
    """
    findings = []
    sources_consulted = 0

    # ---- A) ApprovedClaim Checks ----
    active_claims = ApprovedClaim.objects.filter(workspace=workspace, is_active=True)

    for claim in active_claims:

        # Check for disallowed variations (exaggerated wording the legal team banned)
        if claim.disallowed_variations:
            # disallowed_variations is a comma-separated or newline-separated list
            variations = [
                v.strip()
                for v in re.split(r'[,\n]+', claim.disallowed_variations)
                if v.strip()
            ]
            for variation in variations:
                spans = _find_all_spans(text, variation)
                for start, end in spans:
                    findings.append(RawFinding(
                        finding_type='EVIDENCE_CLAIM',
                        category='Disallowed Claim Variation',
                        flagged_text=text[start:end],
                        start_char=start,
                        end_char=end,
                        severity='HIGH',
                        verification_status='CONTRADICTED',
                        explanation=(
                            f"This phrasing is a disallowed variation of the approved claim "
                            f"'{claim.claim_title}'. "
                            f"Approved statement: \"{claim.permitted_statement}\""
                        ),
                        quoted_passage=claim.permitted_statement,
                        approved_claim_id=claim.id,
                        suggested_correction=claim.permitted_statement,
                        confidence=0.95,
                        is_citation_validated=True,
                    ))

        # Check if a REQUIRED qualifier is missing while the claim keyword appears
        # Strategy: if any word from the permitted_statement appears in the text,
        # check that required qualifiers are also present.
        if claim.required_qualifiers and claim.permitted_statement:
            # Extract key distinctive words from the permitted_statement (>= 5 chars)
            claim_keywords = [
                w.strip('.,;:!?()"\'')
                for w in claim.permitted_statement.split()
                if len(w.strip('.,;:!?()"\'')) >= 5
            ]
            # If any of these keywords appears in the text, the qualifier must also appear
            text_mentions_claim = any(_text_contains(text, kw) for kw in claim_keywords[:5])

            if text_mentions_claim:
                qualifiers = [
                    q.strip()
                    for q in re.split(r'[,\n]+', claim.required_qualifiers)
                    if q.strip()
                ]
                for qualifier in qualifiers:
                    if not _text_contains(text, qualifier):
                        findings.append(RawFinding(
                            finding_type='EVIDENCE_CLAIM',
                            category='Missing Required Qualifier',
                            flagged_text='[Entire submission — missing qualifier]',
                            start_char=0,
                            end_char=len(text),
                            severity='HIGH',
                            verification_status='UNSUPPORTED',
                            explanation=(
                                f"The content appears to reference the claim '{claim.claim_title}' "
                                f"but is missing the required qualifier: \"{qualifier}\"."
                            ),
                            quoted_passage=claim.permitted_statement,
                            approved_claim_id=claim.id,
                            suggested_correction=f"Add required qualifier: '{qualifier}'",
                            confidence=0.85,
                            is_citation_validated=True,
                        ))

    # ---- B) Source Document Evidence Checks ----
    # Load all valid (not expired) source document versions for this workspace
    source_versions = SourceDocumentVersion.objects.filter(
        source_document__workspace=workspace,
        is_approved=True
    ).select_related('source_document')

    for sv in source_versions:
        if not sv.is_currently_valid():
            continue

        sources_consulted += 1

        # Each source version has a JSON list of passage_excerpts:
        # [{ "passage_id": "P1", "text": "EcoVolt batteries last up to 40% longer..." }]
        passages = sv.passage_excerpts if isinstance(sv.passage_excerpts, list) else []

        for passage in passages:
            passage_text = passage.get('text', '')
            if not passage_text:
                continue

            # Extract key phrases from the passage (6+ character words are meaningful)
            key_phrases = [
                w.strip('.,;:!?()"\'')
                for w in passage_text.split()
                if len(w.strip('.,;:!?()"\'')) >= 6
            ]

            # If multiple key phrases from the source appear in the submitted text,
            # this is a relevant match — verify it's correct
            matches = [kp for kp in key_phrases[:8] if _text_contains(text, kp)]

            if len(matches) >= 2:
                # The text references this source — check for contradictions
                # Simple contradiction detector: look for negations near key phrases
                negation_words = ['not', 'never', "doesn't", "don't", "no ", "cannot", "can't", "false"]
                has_negation_near_claim = any(
                    _text_contains(text, f"{neg} {kp}") or _text_contains(text, f"{kp} {neg}")
                    for neg in negation_words
                    for kp in matches
                )

                if has_negation_near_claim:
                    findings.append(RawFinding(
                        finding_type='EVIDENCE_CLAIM',
                        category='Source Contradiction',
                        flagged_text=text[:200] + ('...' if len(text) > 200 else ''),
                        start_char=0,
                        end_char=min(200, len(text)),
                        severity='CRITICAL',
                        verification_status='CONTRADICTED',
                        explanation=(
                            f"The submitted copy appears to contradict verified source "
                            f"'{sv.source_document.document_code}' [{sv.version_label}]. "
                            f"The source states: \"{passage_text[:200]}\""
                        ),
                        quoted_passage=passage_text[:500],
                        source_version_id=sv.id,
                        confidence=0.75,
                        is_citation_validated=True,
                    ))
                else:
                    # Text is consistent with source — create a SUPPORTED finding
                    # (this is a positive validation, useful in the review report)
                    findings.append(RawFinding(
                        finding_type='EVIDENCE_CLAIM',
                        category='Source-Verified Claim',
                        flagged_text=matches[0] if matches else passage_text[:50],
                        start_char=_find_all_spans(text, matches[0])[0][0] if matches and _find_all_spans(text, matches[0]) else 0,
                        end_char=_find_all_spans(text, matches[0])[0][1] if matches and _find_all_spans(text, matches[0]) else 0,
                        severity='LOW',
                        verification_status='SUPPORTED',
                        explanation=(
                            f"This claim is supported by verified source "
                            f"'{sv.source_document.document_code}' [{sv.version_label}]."
                        ),
                        quoted_passage=passage_text[:500],
                        source_version_id=sv.id,
                        confidence=0.90,
                        is_citation_validated=True,
                    ))

    return findings, sources_consulted


# ---------------------------------------------------------------------------
# MAIN ENTRY POINT
# ---------------------------------------------------------------------------

def run_full_review(content_version, workspace) -> EngineResult:
    """
    Executes the complete deterministic review pipeline on a ContentVersion.

    Called by the ReviewRunCreateView in views.py.

    Steps:
      1. Run brand rule checks (prohibited phrases, required terms, tone)
      2. Run claim & evidence verification (approved claims, source documents)
      3. Combine all findings and return the EngineResult

    Args:
        content_version: A ContentVersion model instance (the submitted copy to review)
        workspace: The ClientWorkspace model instance (determines which rules/sources apply)

    Returns:
        EngineResult with all findings and run metadata
    """
    result = EngineResult()
    text = content_version.raw_text or ''

    # Also include OCR-extracted text if an image was provided
    full_text = text
    if content_version.extracted_ocr_text:
        full_text = text + '\n' + content_version.extracted_ocr_text

    try:
        # Step 1: Deterministic brand rule checks
        rule_findings, rules_checked = run_brand_rule_checks(full_text, workspace)
        result.findings.extend(rule_findings)
        result.rules_checked_count = rules_checked

        # Step 2: Evidence & claim verification
        claim_findings, sources_consulted = run_claim_verification(full_text, workspace)
        result.findings.extend(claim_findings)
        result.sources_consulted_count = sources_consulted

    except Exception as e:
        logger.exception("Rule engine encountered an error during review run.")
        result.error_message = str(e)

    return result
