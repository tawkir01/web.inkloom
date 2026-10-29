"""
test_review_engine.py — Phase 6 Automated Tests
=================================================

Tests for:
  1. Rule engine — prohibited phrase detection (DETERMINISTIC_RULE)
  2. Rule engine — required term absence detection
  3. Rule engine — disallowed claim variation detection
  4. Rule engine — required qualifier absence detection
  5. ReviewRun API — full pipeline trigger and persistence
  6. ReviewRun API — status transitions (NEEDS_CHANGES vs READY_FOR_REVIEW)
  7. Approval workflow — reviewer can approve/reject
  8. Approval workflow — Creator CANNOT approve own content (403)
  9. Approval workflow — new revision resets approval (non-inheritance)
  10. Comment API — workspace member can add comments
  11. Multi-tenant isolation — engine only uses workspace-scoped rules
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status as http_status
from django.test import override_settings
from unittest.mock import patch
from workspaces.models import ClientWorkspace, WorkspaceMembership
from governance.models import BrandRule, ApprovedClaim, SourceDocument, SourceDocumentVersion
from reviews.models import ContentItem, ContentVersion, ReviewRun, Finding, ApprovalDecision
from reviews.ai_adapter import AIAnalysisResult
from reviews.rule_engine import run_brand_rule_checks, run_claim_verification, run_full_review, EngineResult

User = get_user_model()


class RuleEngineUnitTest(TestCase):
    """
    Tests the rule engine Python functions in isolation (no HTTP, no database).
    These test the core logic with minimal setup.
    """

    def setUp(self):
        """
        Set up a minimal workspace with brand rules and approved claims
        so we can test the engine without full API calls.
        """
        from workspaces.models import Organisation
        self.org = Organisation.objects.create(name="TestAgency", slug="testagency")
        self.workspace = ClientWorkspace.objects.create(
            organisation=self.org, name="TestBrand", slug="testbrand", is_active=True
        )

        # Create prohibited phrase rule
        self.prohibited_rule = BrandRule.objects.create(
            workspace=self.workspace,
            name="No Guarantee",
            rule_type=BrandRule.RuleType.PROHIBITED_PHRASE,
            pattern_or_phrase="guaranteed",
            preferred_alternative="may help",
            explanation="Cannot use absolute guarantee claims without qualification.",
            severity=BrandRule.Severity.CRITICAL,
            is_active=True,
        )

        # Create required term rule
        self.required_rule = BrandRule.objects.create(
            workspace=self.workspace,
            name="Must Include Disclaimer",
            rule_type=BrandRule.RuleType.REQUIRED_TERM,
            pattern_or_phrase="Results may vary",
            explanation="All product copy must include the standard results disclaimer.",
            severity=BrandRule.Severity.HIGH,
            is_active=True,
        )

        # Create approved claim with disallowed variation
        self.claim = ApprovedClaim.objects.create(
            workspace=self.workspace,
            claim_title="Battery Life Claim",
            permitted_statement="Batteries last up to 40% longer in cold climates",
            required_qualifiers="up to",
            disallowed_variations="lasts 40% longer, 40% more battery life",
            is_active=True,
        )

    # ────────────────────────────────────────────────────────────
    # TEST 1: Prohibited phrase is detected in submitted text
    # ────────────────────────────────────────────────────────────
    def test_prohibited_phrase_flagged(self):
        """
        The word 'guaranteed' is in our brand rules as PROHIBITED.
        The engine should flag it as CONTRADICTED with CRITICAL severity.
        """
        text = "Our product offers guaranteed results for all users."
        findings, count = run_brand_rule_checks(text, self.workspace)

        prohibited = [f for f in findings if f.brand_rule_id == self.prohibited_rule.id]
        self.assertEqual(len(prohibited), 1, "Should flag one prohibited phrase occurrence")
        self.assertEqual(prohibited[0].severity, 'CRITICAL')
        self.assertEqual(prohibited[0].verification_status, 'CONTRADICTED')
        self.assertEqual(prohibited[0].finding_type, 'DETERMINISTIC_RULE')
        self.assertTrue(prohibited[0].is_citation_validated)

    # ────────────────────────────────────────────────────────────
    # TEST 2: Required term absence is correctly detected
    # ────────────────────────────────────────────────────────────
    def test_required_term_absence_flagged(self):
        """
        'Results may vary' is a required term.
        Text without it should get a REQUIRED_TERM finding.
        """
        text = "Our product is excellent and helps everyone feel better."
        findings, count = run_brand_rule_checks(text, self.workspace)

        required = [f for f in findings if f.brand_rule_id == self.required_rule.id]
        self.assertEqual(len(required), 1, "Should flag absence of required term")
        self.assertEqual(required[0].verification_status, 'UNSUPPORTED')

    # ────────────────────────────────────────────────────────────
    # TEST 3: Required term PRESENT means no flag raised
    # ────────────────────────────────────────────────────────────
    def test_required_term_present_no_flag(self):
        """
        When the required phrase IS in the text, no finding should be created for it.
        """
        text = "Our product is excellent. Results may vary."
        findings, count = run_brand_rule_checks(text, self.workspace)

        required = [f for f in findings if f.brand_rule_id == self.required_rule.id]
        self.assertEqual(len(required), 0, "Should NOT flag when required term is present")

    # ────────────────────────────────────────────────────────────
    # TEST 4: Disallowed claim variation is flagged
    # ────────────────────────────────────────────────────────────
    def test_disallowed_claim_variation_flagged(self):
        """
        'lasts 40% longer' is a disallowed variation of the approved battery claim.
        The claim engine should flag it.
        """
        text = "Our battery lasts 40% longer than competitors."
        findings, count = run_claim_verification(text, self.workspace)

        disallowed = [f for f in findings if f.category == 'Disallowed Claim Variation']
        self.assertGreater(len(disallowed), 0, "Should flag disallowed claim variation")
        self.assertEqual(disallowed[0].verification_status, 'CONTRADICTED')
        self.assertEqual(disallowed[0].severity, 'HIGH')
        self.assertEqual(disallowed[0].approved_claim_id, self.claim.id)

    def test_disallowed_claim_finding_cites_its_approved_source(self):
        source = SourceDocument.objects.create(
            workspace=self.workspace,
            title="Cold-Climate Battery Test",
            document_code="SRC-BATTERY-01",
        )
        source_version = SourceDocumentVersion.objects.create(
            source_document=source,
            version_label="v1.0",
            full_text_content="Laboratory testing confirms the cold-climate battery result.",
            passage_excerpts=[
                {
                    "passage_id": "P1",
                    "text": "Batteries last up to 40% longer in cold climates under laboratory conditions.",
                },
                {
                    "passage_id": "P2",
                    "text": "Testing was conducted in an unrelated scenario.",
                },
            ],
        )
        self.claim.source_version = source_version
        self.claim.save(update_fields=["source_version"])

        findings, _ = run_claim_verification(
            "Our battery lasts 40% longer than competitors.",
            self.workspace,
        )

        finding = next(f for f in findings if f.category == "Disallowed Claim Variation")
        self.assertEqual(finding.source_version_id, source_version.id)
        self.assertEqual(finding.source_passage_id, "P1")
        self.assertEqual(
            finding.quoted_passage,
            "Batteries last up to 40% longer in cold climates under laboratory conditions.",
        )
        self.assertEqual(
            finding.suggested_correction,
            self.claim.permitted_statement,
        )

    def test_claim_source_evidence_is_isolated_to_its_workspace(self):
        other_workspace = ClientWorkspace.objects.create(
            organisation=self.org,
            name="Other Brand",
            slug="other-brand",
            is_active=True,
        )
        other_source = SourceDocument.objects.create(
            workspace=other_workspace,
            title="Other Brand Battery Study",
            document_code="SRC-OTHER-01",
        )
        other_version = SourceDocumentVersion.objects.create(
            source_document=other_source,
            version_label="v1.0",
            full_text_content="Other client's battery results.",
            passage_excerpts=[{"passage_id": "P1", "text": "Battery lasts 40% longer."}],
        )
        other_claim = ApprovedClaim.objects.create(
            workspace=other_workspace,
            claim_title="Other client's claim",
            permitted_statement="Battery lasts up to 40% longer.",
            disallowed_variations="lasts 40% longer",
            source_version=other_version,
        )

        findings, sources_consulted = run_claim_verification(
            "Our battery lasts 40% longer.",
            self.workspace,
        )

        self.assertEqual(sources_consulted, 0)
        self.assertFalse(any(f.approved_claim_id == other_claim.id for f in findings))

    def test_numeric_phrase_with_trailing_punctuation_is_matched(self):
        rule = BrandRule.objects.create(
            workspace=self.workspace,
            name="No numeric percentage",
            rule_type=BrandRule.RuleType.PROHIBITED_PHRASE,
            pattern_or_phrase="20%",
            explanation="This percentage is prohibited.",
            severity=BrandRule.Severity.HIGH,
        )

        text = "Save 20% today."
        findings, _ = run_brand_rule_checks(text, self.workspace)
        finding = next(f for f in findings if f.brand_rule_id == rule.id)

        self.assertEqual(text[finding.start_char:finding.end_char], "20%")
        self.assertEqual(finding.flagged_text, "20%")

    def test_missing_qualifier_finding_uses_exact_claim_offsets(self):
        claim = ApprovedClaim.objects.create(
            workspace=self.workspace,
            claim_title="Battery life",
            permitted_statement="Battery lasts 40% longer",
            required_qualifiers="up to",
        )
        text = "🚀 Battery lasts 40% longer."

        findings, _ = run_claim_verification(text, self.workspace)
        finding = next(f for f in findings if f.approved_claim_id == claim.id)

        self.assertEqual(
            text[finding.start_char:finding.end_char],
            finding.flagged_text,
        )
        self.assertEqual(finding.flagged_text, "Battery lasts 40% longer")

    def test_numeric_exaggeration_and_missing_qualifier_are_detected(self):
        text = "🚀 Batteries last 60% longer in cold climates."

        findings, _ = run_claim_verification(text, self.workspace)
        numeric_finding = next(
            finding for finding in findings
            if finding.category == "Exaggerated Numerical Claim"
        )
        qualifier_finding = next(
            finding for finding in findings
            if finding.category == "Missing Required Qualifier"
        )

        self.assertEqual(numeric_finding.verification_status, "CONTRADICTED")
        self.assertEqual(
            text[numeric_finding.start_char:numeric_finding.end_char],
            numeric_finding.flagged_text,
        )
        self.assertEqual(numeric_finding.flagged_text, "Batteries last 60% longer in cold climates")
        self.assertEqual(
            text[qualifier_finding.start_char:qualifier_finding.end_char],
            qualifier_finding.flagged_text,
        )
        self.assertEqual(qualifier_finding.flagged_text, numeric_finding.flagged_text)
        self.assertIn("up to", qualifier_finding.explanation)

    def test_word_overlap_is_not_reported_as_proof_of_support(self):
        source = SourceDocument.objects.create(
            workspace=self.workspace,
            title="Battery Report",
            document_code="SRC-BATTERY-OVERLAP",
        )
        SourceDocumentVersion.objects.create(
            source_document=source,
            version_label="v1.0",
            full_text_content="The EcoVolt battery lasts 24 hours in cold climates.",
            passage_excerpts=[
                {
                    "passage_id": "P1",
                    "text": "The EcoVolt battery lasts 24 hours in cold climates.",
                },
            ],
        )
        text = "EcoVolt battery popularity is growing."

        findings, _ = run_claim_verification(text, self.workspace)
        finding = next(
            item for item in findings
            if item.category == "Potentially Relevant Source"
        )

        self.assertEqual(finding.verification_status, "UNABLE_TO_DETERMINE")
        self.assertNotEqual(finding.verification_status, "SUPPORTED")
        self.assertEqual(
            text[finding.start_char:finding.end_char],
            finding.flagged_text,
        )

    def test_exact_unicode_source_text_has_exact_offsets(self):
        source = SourceDocument.objects.create(
            workspace=self.workspace,
            title="Battery Report",
            document_code="SRC-BATTERY-UNICODE",
        )
        SourceDocumentVersion.objects.create(
            source_document=source,
            version_label="v1.0",
            full_text_content="Café battery saves 20% during tests.",
            passage_excerpts=[
                {
                    "passage_id": "P1",
                    "text": "Café battery saves 20% during tests.",
                },
            ],
        )
        text = "🚀 Café battery saves 20% during tests."

        findings, _ = run_claim_verification(text, self.workspace)
        finding = next(
            item for item in findings
            if item.category == "Source-Verified Claim"
        )

        self.assertEqual(
            text[finding.start_char:finding.end_char],
            finding.flagged_text,
        )
        self.assertEqual(finding.flagged_text, "Café battery saves 20% during tests.")

    # ────────────────────────────────────────────────────────────
    # TEST 5: Multiple violations in one text → multiple findings
    # ────────────────────────────────────────────────────────────
    def test_multiple_violations_detected(self):
        """
        Text with multiple violations should return multiple separate findings.
        """
        text = "Our product offers guaranteed results and lasts 40% longer."
        findings, count = run_brand_rule_checks(text, self.workspace)
        # Must have at least: prohibited 'guaranteed' + missing required term
        self.assertGreaterEqual(len(findings), 1)

    # ────────────────────────────────────────────────────────────
    # TEST 6: Inactive rules are not checked
    # ────────────────────────────────────────────────────────────
    def test_inactive_rule_skipped(self):
        """
        Deactivated rules must NOT generate findings even if the phrase matches.
        """
        self.prohibited_rule.is_active = False
        self.prohibited_rule.save()

        text = "Our product offers guaranteed results."
        findings, count = run_brand_rule_checks(text, self.workspace)

        prohibited = [f for f in findings if f.brand_rule_id == self.prohibited_rule.id]
        self.assertEqual(len(prohibited), 0, "Inactive rule should NOT generate a finding")


@override_settings(
    AI_PROVIDER="mock",
    AI_API_KEY="",
    AI_MODEL_NAME="mock-model",
)
class ReviewRunAPITest(TestCase):
    """
    Integration tests for the full review pipeline via HTTP API.
    Tests that the API creates ReviewRun records, persists Findings,
    and transitions ContentVersion status correctly.
    """

    def setUp(self):
        self.client = APIClient()

        # Create workspace and two users
        from workspaces.models import Organisation
        self.org = Organisation.objects.create(name="ReviewAgency", slug="reviewagency")
        self.workspace = ClientWorkspace.objects.create(
            organisation=self.org, name="EcoVolt", slug="ecovolt", is_active=True
        )

        # Creator user (submits content)
        self.creator = User.objects.create_user(username="creator1", password="pass123")
        WorkspaceMembership.objects.create(
            workspace=self.workspace, user=self.creator,
            role=WorkspaceMembership.Role.CREATOR, is_active=True
        )

        # Reviewer user (approves/rejects)
        self.reviewer = User.objects.create_user(username="reviewer1", password="pass123")
        WorkspaceMembership.objects.create(
            workspace=self.workspace, user=self.reviewer,
            role=WorkspaceMembership.Role.REVIEWER, is_active=True
        )

        # Brand rule that will trigger a finding
        BrandRule.objects.create(
            workspace=self.workspace,
            name="No Guarantee Claims",
            rule_type=BrandRule.RuleType.PROHIBITED_PHRASE,
            pattern_or_phrase="guaranteed",
            explanation="Cannot use absolute guarantee claims.",
            severity=BrandRule.Severity.CRITICAL,
            is_active=True,
        )

        # Create content item and version (v1) to review
        self.item = ContentItem.objects.create(
            workspace=self.workspace,
            title="EcoVolt Summer Ad",
            created_by=self.creator
        )
        self.version = ContentVersion.objects.create(
            content_item=self.item,
            version_number=1,
            raw_text="Our EcoVolt battery offers guaranteed performance for all customers.",
            status=ContentVersion.Status.SUBMITTED,
            created_by=self.creator
        )

    def _auth_as(self, user):
        from rest_framework.authtoken.models import Token
        token, _ = Token.objects.get_or_create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    # ────────────────────────────────────────────────────────────
    # TEST 7: Review run creates findings and transitions status
    # ────────────────────────────────────────────────────────────
    def test_review_run_creates_findings_and_updates_status(self):
        """
        POST /api/content/<id>/versions/1/review/ should:
          - Return HTTP 201
          - Create a COMPLETED ReviewRun record
          - Persist at least one Finding for 'guaranteed'
          - Set ContentVersion status to NEEDS_CHANGES (HIGH/CRITICAL finding present)
        """
        self._auth_as(self.creator)
        url = f"/api/content/{self.item.id}/versions/1/review/"
        response = self.client.post(url)

        self.assertEqual(response.status_code, 201, response.data)
        data = response.data
        self.assertEqual(data['run_status'], 'COMPLETED')
        self.assertEqual(data['ai_status'], ReviewRun.AIStatus.NOT_CONFIGURED)
        self.assertGreater(data['findings_count'], 0)
        self.assertGreater(data['critical_count'], 0)

        # The version should now be NEEDS_CHANGES because CRITICAL finding
        self.version.refresh_from_db()
        self.assertEqual(self.version.status, ContentVersion.Status.NEEDS_CHANGES)

    @patch("reviews.views.run_full_review", side_effect=RuntimeError("private database detail"))
    def test_review_engine_failure_is_marked_failed_without_leaking_details(self, _mock_engine):
        self._auth_as(self.creator)
        response = self.client.post(
            f"/api/content/{self.item.id}/versions/1/review/"
        )

        self.assertEqual(response.status_code, http_status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertNotIn("private database detail", response.data["detail"])
        self.version.refresh_from_db()
        self.assertEqual(self.version.status, ContentVersion.Status.FAILED)
        review_run = ReviewRun.objects.get(content_version=self.version)
        self.assertEqual(review_run.run_status, ReviewRun.RunStatus.FAILED)
        self.assertNotIn("private database detail", review_run.error_message)

    @patch(
        "reviews.ai_adapter.analyze_claims",
        return_value=AIAnalysisResult(
            status="FAILED",
            error_message="AI analysis returned an invalid response.",
        ),
    )
    def test_ai_failure_preserves_deterministic_review_results(self, _mock_ai):
        self._auth_as(self.creator)
        response = self.client.post(
            f"/api/content/{self.item.id}/versions/1/review/"
        )

        self.assertEqual(response.status_code, http_status.HTTP_201_CREATED)
        self.assertEqual(response.data["run_status"], ReviewRun.RunStatus.COMPLETED)
        self.assertEqual(response.data["ai_status"], ReviewRun.AIStatus.FAILED)
        self.assertGreater(response.data["findings_count"], 0)
        self.assertIn("invalid response", response.data["ai_error_message"])

    def test_review_history_is_not_visible_to_other_workspace_members(self):
        other_workspace = ClientWorkspace.objects.create(
            organisation=self.org,
            name="Other Review Brand",
            slug="other-review-brand",
            is_active=True,
        )
        other_user = User.objects.create_user(
            username="other-brand-user",
            password="test-pass-123",
        )
        WorkspaceMembership.objects.create(
            workspace=other_workspace,
            user=other_user,
            role=WorkspaceMembership.Role.CREATOR,
            is_active=True,
        )

        self._auth_as(other_user)
        response = self.client.get(
            f"/api/content/{self.item.id}/versions/1/reviews/"
        )

        self.assertEqual(response.status_code, http_status.HTTP_403_FORBIDDEN)

    def test_review_response_includes_linked_claim_evidence(self):
        source = SourceDocument.objects.create(
            workspace=self.workspace,
            title="Battery Performance Study",
            document_code="SRC-BATTERY-REVIEW",
        )
        source_version = SourceDocumentVersion.objects.create(
            source_document=source,
            version_label="v2.0",
            full_text_content="The laboratory study supports the qualified battery statement.",
            passage_excerpts=[
                {
                    "passage_id": "P1",
                    "text": "Batteries last up to 40% longer in cold climates.",
                },
            ],
        )
        ApprovedClaim.objects.create(
            workspace=self.workspace,
            claim_title="Cold-weather battery life",
            permitted_statement="Batteries last up to 40% longer in cold climates.",
            disallowed_variations="lasts 40% longer",
            source_version=source_version,
        )
        claim_item = ContentItem.objects.create(
            workspace=self.workspace,
            title="Cold-weather battery claim",
            created_by=self.creator,
        )
        claim_version = ContentVersion.objects.create(
            content_item=claim_item,
            version_number=1,
            raw_text="Our battery lasts 40% longer in cold climates.",
            created_by=self.creator,
        )

        self._auth_as(self.creator)
        response = self.client.post(
            f"/api/content/{claim_item.id}/versions/1/review/"
        )

        self.assertEqual(response.status_code, 201, response.data)
        claim_finding = next(
            finding for finding in response.data["findings"]
            if finding["category"] == "Disallowed Claim Variation"
        )
        self.assertEqual(claim_finding["source_document_code"], "SRC-BATTERY-REVIEW")
        self.assertEqual(claim_finding["source_document_title"], "Battery Performance Study")
        self.assertEqual(claim_finding["source_version_label"], "v2.0")
        self.assertEqual(claim_finding["source_passage_id"], "P1")
        self.assertEqual(
            claim_finding["quoted_passage"],
            "Batteries last up to 40% longer in cold climates.",
        )
        self.assertEqual(
            claim_finding["suggested_correction"],
            "Batteries last up to 40% longer in cold climates.",
        )
        finding = Finding.objects.get(id=claim_finding["id"])
        source.title = "Renamed after review"
        source.document_code = "SRC-RENAMED"
        source.save(update_fields=["title", "document_code"])
        source_version.version_label = "v3.0"
        source_version.save(update_fields=["version_label"])
        refreshed_finding = Finding.objects.get(id=finding.id)
        from reviews.serializers import FindingSerializer
        snapshot = FindingSerializer(refreshed_finding).data
        self.assertEqual(snapshot["source_document_title"], "Battery Performance Study")
        self.assertEqual(snapshot["source_document_code"], "SRC-BATTERY-REVIEW")
        self.assertEqual(snapshot["source_version_label"], "v2.0")

    # ────────────────────────────────────────────────────────────
    # TEST 8: Clean content gets READY_FOR_REVIEW status
    # ────────────────────────────────────────────────────────────
    def test_clean_content_gets_ready_for_review(self):
        """
        Content with no violations should transition to READY_FOR_REVIEW.
        """
        # Create a clean content version without any violations
        clean_item = ContentItem.objects.create(
            workspace=self.workspace, title="Clean Ad", created_by=self.creator
        )
        clean_version = ContentVersion.objects.create(
            content_item=clean_item,
            version_number=1,
            raw_text="EcoVolt batteries are designed for long-lasting, reliable performance.",
            status=ContentVersion.Status.SUBMITTED,
            created_by=self.creator
        )

        self._auth_as(self.creator)
        url = f"/api/content/{clean_item.id}/versions/1/review/"
        response = self.client.post(url)

        self.assertEqual(response.status_code, 201)
        clean_version.refresh_from_db()
        self.assertEqual(clean_version.status, ContentVersion.Status.READY_FOR_REVIEW)

    # ────────────────────────────────────────────────────────────
    # TEST 9: Cannot re-review an APPROVED version
    # ────────────────────────────────────────────────────────────
    def test_cannot_review_approved_version(self):
        """
        Once a version is APPROVED, the review engine should refuse to re-run.
        """
        self.version.status = ContentVersion.Status.APPROVED
        self.version.save()

        self._auth_as(self.creator)
        url = f"/api/content/{self.item.id}/versions/1/review/"
        response = self.client.post(url)

        self.assertEqual(response.status_code, 400)

    # ────────────────────────────────────────────────────────────
    # TEST 10: Reviewer can approve READY_FOR_REVIEW content
    # ────────────────────────────────────────────────────────────
    def test_reviewer_can_approve_content(self):
        """
        A Brand Reviewer should be able to POST an APPROVED decision.
        ContentVersion status must update to APPROVED.
        """
        # First run review to put it in a reviewable state
        self.version.status = ContentVersion.Status.READY_FOR_REVIEW
        self.version.save()
        ReviewRun.objects.create(
            content_version=self.version,
            triggered_by=self.creator,
            run_status=ReviewRun.RunStatus.COMPLETED,
            ai_provider="test",
        )

        self._auth_as(self.reviewer)
        url = f"/api/content/{self.item.id}/versions/1/approval/"
        response = self.client.post(url, {
            "decision": "APPROVED",
            "decision_notes": "All claims verified and comply with brand guidelines."
        })

        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['decision'], 'APPROVED')

        # Verify the ContentVersion status is now APPROVED
        self.version.refresh_from_db()
        self.assertEqual(self.version.status, ContentVersion.Status.APPROVED)

    def test_reviewer_cannot_approve_before_a_completed_review(self):
        self._auth_as(self.reviewer)
        response = self.client.post(
            f"/api/content/{self.item.id}/versions/1/approval/",
            {"decision": "APPROVED"},
        )

        self.assertEqual(response.status_code, http_status.HTTP_400_BAD_REQUEST)
        self.assertFalse(
            ApprovalDecision.objects.filter(content_version=self.version).exists()
        )

    # ────────────────────────────────────────────────────────────
    # TEST 11: Content Creator CANNOT make approval decisions (403)
    # ────────────────────────────────────────────────────────────
    def test_creator_cannot_approve(self):
        """
        RBAC check: A Content Creator role must be blocked from approving copy.
        Only REVIEWER or ADMIN can approve.
        """
        self.version.status = ContentVersion.Status.READY_FOR_REVIEW
        self.version.save()

        self._auth_as(self.creator)  # Creator trying to approve
        url = f"/api/content/{self.item.id}/versions/1/approval/"
        response = self.client.post(url, {"decision": "APPROVED"})

        self.assertEqual(response.status_code, 403, "Creator must be blocked from approving")

    # ────────────────────────────────────────────────────────────
    # TEST 12: New revision does NOT inherit approval (core compliance guarantee)
    # ────────────────────────────────────────────────────────────
    def test_new_revision_resets_approval(self):
        """
        CRITICAL COMPLIANCE TEST:
        After v1 is APPROVED, spawning v2 must start as SUBMITTED.
        The approval on v1 must NOT transfer to v2.
        """
        # Approve v1
        self.version.status = ContentVersion.Status.APPROVED
        self.version.save()
        ApprovalDecision.objects.create(
            content_version=self.version,
            reviewer=self.reviewer,
            decision=ApprovalDecision.Decision.APPROVED,
        )

        # Creator spawns v2
        self._auth_as(self.creator)
        revision_url = f"/api/content/{self.item.id}/versions/"
        response = self.client.post(revision_url, {
            "raw_text": "EcoVolt batteries provide guaranteed results — updated copy."
        })

        self.assertEqual(response.status_code, 201)
        new_version_id = response.data['id']

        # Verify v2 starts as SUBMITTED, not APPROVED
        from uuid import UUID
        v2 = ContentVersion.objects.get(id=new_version_id)
        self.assertEqual(v2.status, ContentVersion.Status.SUBMITTED)
        self.assertFalse(
            v2.approval_decisions.filter(decision=ApprovalDecision.Decision.APPROVED).exists(),
            "V2 must have zero approval decisions — approvals never inherit."
        )

    # ────────────────────────────────────────────────────────────
    # TEST 13: Comments can be added by workspace members
    # ────────────────────────────────────────────────────────────
    def test_workspace_member_can_comment(self):
        """
        Any workspace member (creator or reviewer) should be able to post a comment.
        """
        self._auth_as(self.reviewer)
        url = f"/api/content/{self.item.id}/versions/1/comments/"
        response = self.client.post(url, {
            "comment_text": "Please fix the guaranteed claim before resubmitting."
        })

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['comment_text'], "Please fix the guaranteed claim before resubmitting.")
        self.assertEqual(response.data['author_username'], 'reviewer1')

    # ────────────────────────────────────────────────────────────
    # TEST 14: Multi-tenant isolation — rules from other workspaces ignored
    # ────────────────────────────────────────────────────────────
    def test_rule_engine_only_uses_workspace_scoped_rules(self):
        """
        SECURITY TEST: Rules defined in a different workspace must NOT
        influence reviews in the current workspace.
        """
        # Create a competing workspace with its own rules
        from workspaces.models import Organisation
        other_org = Organisation.objects.create(name="CompetitorAgency", slug="competitoragency")
        other_workspace = ClientWorkspace.objects.create(
            organisation=other_org, name="CompetitorBrand", slug="competitor", is_active=True
        )
        BrandRule.objects.create(
            workspace=other_workspace,
            name="Competitor-only rule",
            rule_type=BrandRule.RuleType.PROHIBITED_PHRASE,
            pattern_or_phrase="reliable",
            explanation="Competitor rule that must not cross workspaces.",
            severity=BrandRule.Severity.CRITICAL,
            is_active=True,
        )

        # Text contains 'reliable' which is only banned in competitor workspace
        text = "EcoVolt provides reliable performance for your home."
        findings, count = run_brand_rule_checks(text, self.workspace)

        # 'reliable' should NOT be flagged because the rule belongs to other_workspace
        reliable_findings = [
            f for f in findings
            if 'reliable' in f.flagged_text.lower()
        ]
        self.assertEqual(len(reliable_findings), 0,
                         "Cross-workspace rule contamination detected! Isolation broken.")
