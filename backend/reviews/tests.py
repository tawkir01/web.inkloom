import hashlib
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from workspaces.models import Organisation, ClientWorkspace, WorkspaceMembership
from governance.models import BrandRule, ApprovedClaim, SourceDocument, SourceDocumentVersion
from reviews.models import ContentItem, ContentVersion, ReviewRun, Finding, ApprovalDecision

User = get_user_model()

class GovernanceAndReviewSchemaTests(TestCase):
    def setUp(self):
        self.org = Organisation.objects.create(name="Aura Agency")
        self.workspace = ClientWorkspace.objects.create(
            organisation=self.org,
            name="EcoVolt"
        )
        self.creator = User.objects.create_user(username="creator_tim", password="password123")
        self.reviewer = User.objects.create_user(username="reviewer_sarah", password="password123")

        WorkspaceMembership.objects.create(
            workspace=self.workspace,
            user=self.creator,
            role=WorkspaceMembership.Role.CREATOR
        )
        WorkspaceMembership.objects.create(
            workspace=self.workspace,
            user=self.reviewer,
            role=WorkspaceMembership.Role.REVIEWER
        )

        # Approved source document & version
        self.source_doc = SourceDocument.objects.create(
            workspace=self.workspace,
            title="EcoVolt 2025 Field Efficiency Report",
            document_code="SRC-EV-2025"
        )
        self.source_version = SourceDocumentVersion.objects.create(
            source_document=self.source_doc,
            version_label="v1.0",
            full_text_content="Field testing confirmed typical customers save up to 20% on monthly electric bills.",
            passage_excerpts=[
                {"passage_id": "P-EV-01", "text": "save up to 20% on monthly electric bills"}
            ]
        )

        # Brand Rule
        self.rule = BrandRule.objects.create(
            workspace=self.workspace,
            name="No Guaranteed Absolute Savings",
            rule_type=BrandRule.RuleType.PROHIBITED_PHRASE,
            pattern_or_phrase="guaranteed 50%",
            preferred_alternative="save up to 20%",
            explanation="Unsubstantiated guarantee violates FTC and brand compliance.",
            severity=BrandRule.Severity.CRITICAL
        )

    def test_content_version_computes_sha256_checksum(self):
        """ContentVersion must automatically generate an SHA-256 hash of submitted copy."""
        item = ContentItem.objects.create(
            workspace=self.workspace,
            title="Summer Heat Wave Social Ad",
            created_by=self.creator
        )
        sample_text = "EcoVolt smart panels deliver guaranteed 50% savings!"
        expected_hash = hashlib.sha256(sample_text.encode('utf-8')).hexdigest()

        version_1 = ContentVersion.objects.create(
            content_item=item,
            version_number=1,
            raw_text=sample_text,
            created_by=self.creator
        )

        self.assertEqual(version_1.checksum_sha256, expected_hash)
        self.assertEqual(version_1.status, ContentVersion.Status.SUBMITTED)

    def test_content_version_snapshot_cannot_be_modified(self):
        item = ContentItem.objects.create(
            workspace=self.workspace,
            title="Immutable copy",
            created_by=self.creator,
        )
        version = ContentVersion.objects.create(
            content_item=item,
            version_number=1,
            raw_text="Original submitted copy.",
            created_by=self.creator,
        )

        version.raw_text = "Changed copy."
        with self.assertRaises(ValidationError):
            version.save()

        version.refresh_from_db()
        self.assertEqual(version.raw_text, "Original submitted copy.")
    def test_duplicate_version_number_rejected_by_database(self):
        """Database constraint must prevent two versions having the same version_number on an item."""
        item = ContentItem.objects.create(
            workspace=self.workspace,
            title="Quarterly Email Newsletter",
            created_by=self.creator
        )
        ContentVersion.objects.create(
            content_item=item,
            version_number=1,
            raw_text="Version 1 copy",
            created_by=self.creator
        )
        with self.assertRaises(IntegrityError):
            ContentVersion.objects.create(
                content_item=item,
                version_number=1,
                raw_text="Another version with same number",
                created_by=self.creator
            )

    def test_approval_decision_bound_to_exact_version(self):
        """
        Critical rule: An approval is strictly bound to a specific ContentVersion.
        When a new version (v2) is submitted, it does NOT inherit v1's approval.
        """
        item = ContentItem.objects.create(
            workspace=self.workspace,
            title="Clean Energy Campaign",
            created_by=self.creator
        )
        v1 = ContentVersion.objects.create(
            content_item=item,
            version_number=1,
            raw_text="Save up to 20% on energy costs with EcoVolt.",
            created_by=self.creator,
            status=ContentVersion.Status.APPROVED
        )

        decision = ApprovalDecision.objects.create(
            content_version=v1,
            reviewer=self.reviewer,
            decision=ApprovalDecision.Decision.APPROVED,
            decision_notes="Citations validated against SRC-EV-2025 v1.0."
        )

        self.assertEqual(decision.content_version, v1)
        self.assertEqual(v1.status, ContentVersion.Status.APPROVED)

        # Now creator edits the copy to produce v2
        v2 = ContentVersion.objects.create(
            content_item=item,
            version_number=2,
            raw_text="Save up to 20% and get free installation this weekend!",
            created_by=self.creator,
            status=ContentVersion.Status.SUBMITTED
        )

        # Verify that v2 does NOT inherit approval status from v1
        self.assertEqual(v2.status, ContentVersion.Status.SUBMITTED)
        self.assertEqual(v2.approval_decisions.count(), 0)
        self.assertEqual(v1.approval_decisions.count(), 1)

    def test_finding_links_to_source_version(self):
        """Findings can link directly to a specific version of a source document."""
        item = ContentItem.objects.create(
            workspace=self.workspace,
            title="Press Release",
            created_by=self.creator
        )
        v1 = ContentVersion.objects.create(
            content_item=item,
            version_number=1,
            raw_text="EcoVolt guarantees 50% savings.",
            created_by=self.creator
        )
        run = ReviewRun.objects.create(
            content_version=v1,
            run_status=ReviewRun.RunStatus.COMPLETED
        )
        finding = Finding.objects.create(
            review_run=run,
            content_version=v1,
            category="Exaggerated Claim",
            flagged_text="guarantees 50% savings",
            severity=Finding.Severity.CRITICAL,
            verification_status=Finding.VerificationStatus.CONTRADICTED,
            explanation="Report confirms up to 20%, not 50%.",
            quoted_passage="save up to 20% on monthly electric bills",
            source_version=self.source_version,
            is_citation_validated=True
        )

        self.assertEqual(finding.source_version.version_label, "v1.0")
        self.assertTrue(finding.is_citation_validated)
