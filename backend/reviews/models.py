import uuid
import hashlib
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from workspaces.models import ClientWorkspace
from governance.models import SourceDocumentVersion, BrandRule, ApprovedClaim

class ContentItem(models.Model):
    """
    Top-level container for a marketing asset (e.g. 'EcoVolt Spring 2026 Ad Campaign').
    Houses all sequential, immutable ContentVersions.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(
        ClientWorkspace, 
        on_delete=models.CASCADE, 
        related_name='content_items'
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='submitted_content_items'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['workspace', '-updated_at']),
        ]

    def __str__(self):
        return f"{self.title} ({self.workspace.name})"


class ContentVersion(models.Model):
    """
    An IMMUTABLE snapshot of submitted marketing content.
    Every edit creates a new numbered version (v1, v2, v3).
    Approvals are bound strictly to a specific version. Later edits never inherit approval.
    """
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        SUBMITTED = 'SUBMITTED', 'Submitted'
        PROCESSING = 'PROCESSING', 'Processing'
        NEEDS_CHANGES = 'NEEDS_CHANGES', 'Needs Changes'
        READY_FOR_REVIEW = 'READY_FOR_REVIEW', 'Ready For Review'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
        FAILED = 'FAILED', 'Processing Failed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content_item = models.ForeignKey(
        ContentItem, 
        on_delete=models.CASCADE, 
        related_name='versions'
    )
    version_number = models.PositiveIntegerField(default=1)
    raw_text = models.TextField(help_text="The exact text submitted for governance check")
    image_file = models.FileField(
        upload_to='submissions/%Y/%m/', 
        blank=True, 
        null=True,
        help_text="Optional marketing visual/ad asset"
    )
    extracted_ocr_text = models.TextField(
        blank=True, 
        help_text="Text extracted via OCR if image was supplied"
    )
    ocr_confidence = models.FloatField(
        null=True, 
        blank=True,
        help_text="Confidence level (0.0 - 1.0) of OCR extraction"
    )
    status = models.CharField(
        max_length=32, 
        choices=Status.choices, 
        default=Status.SUBMITTED
    )
    checksum_sha256 = models.CharField(
        max_length=64, 
        blank=True,
        help_text="Cryptographic integrity hash guaranteeing content immutability"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='created_content_versions'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('content_item', 'version_number')
        ordering = ['-version_number']
        indexes = [
            models.Index(fields=['content_item', 'status']),
            models.Index(fields=['status']),
        ]

    def save(self, *args, **kwargs):
        if self._state.adding:
            self.checksum_sha256 = self._calculate_checksum()
        else:
            existing = type(self).objects.get(pk=self.pk)
            original_snapshot = (
                existing.content_item_id,
                existing.version_number,
                existing.raw_text,
                existing.image_file.name if existing.image_file else '',
                existing.extracted_ocr_text,
                existing.ocr_confidence,
                existing.created_by_id,
            )
            updated_snapshot = (
                self.content_item_id,
                self.version_number,
                self.raw_text,
                self.image_file.name if self.image_file else '',
                self.extracted_ocr_text,
                self.ocr_confidence,
                self.created_by_id,
            )
            if updated_snapshot != original_snapshot:
                raise ValidationError("Submitted content versions are immutable; create a revision instead.")

            expected_checksum = existing._calculate_checksum()
            if existing.checksum_sha256 and existing.checksum_sha256 != expected_checksum:
                raise ValidationError("The stored content version checksum does not match its snapshot.")
            if self.checksum_sha256 != existing.checksum_sha256:
                raise ValidationError("The content version checksum cannot be changed.")
            if not existing.checksum_sha256:
                self.checksum_sha256 = expected_checksum
                update_fields = kwargs.get('update_fields')
                if update_fields is not None:
                    kwargs['update_fields'] = set(update_fields) | {'checksum_sha256'}

        super().save(*args, **kwargs)

    def _calculate_checksum(self):
        hasher = hashlib.sha256()
        hasher.update((self.raw_text or '').encode('utf-8'))
        if self.extracted_ocr_text:
            hasher.update(self.extracted_ocr_text.encode('utf-8'))
        return hasher.hexdigest()

    def __str__(self):
        return f"{self.content_item.title} [v{self.version_number}] ({self.get_status_display()})"


class ReviewRun(models.Model):
    """
    Execution record of an automated governance review pipeline on an exact ContentVersion.
    """
    class RunStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        RUNNING = 'RUNNING', 'Running'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'

    class AIStatus(models.TextChoices):
        NOT_CONFIGURED = 'NOT_CONFIGURED', 'Not Configured'
        RUNNING = 'RUNNING', 'Running'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content_version = models.ForeignKey(
        ContentVersion, 
        on_delete=models.CASCADE, 
        related_name='review_runs'
    )
    triggered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    run_status = models.CharField(
        max_length=32, 
        choices=RunStatus.choices, 
        default=RunStatus.PENDING
    )
    ai_provider = models.CharField(max_length=64, default='mock')
    ai_model = models.CharField(max_length=128, blank=True)
    ai_status = models.CharField(
        max_length=32,
        choices=AIStatus.choices,
        default=AIStatus.NOT_CONFIGURED,
    )
    ai_error_message = models.TextField(blank=True)
    rules_checked_count = models.IntegerField(default=0)
    sources_consulted_count = models.IntegerField(default=0)
    raw_model_response = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Review for {self.content_version} @ {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class Finding(models.Model):
    """
    Specific flagged brand or claim issue discovered during a ReviewRun.
    Anchored to exact character spans in the submitted copy and validated against real sources.
    """
    class FindingType(models.TextChoices):
        DETERMINISTIC_RULE = 'DETERMINISTIC_RULE', 'Deterministic Rule Check'
        EVIDENCE_CLAIM = 'EVIDENCE_CLAIM', 'Evidence & Claim Verification'
        IMAGE_OCR = 'IMAGE_OCR', 'Image Text OCR Finding'

    class Severity(models.TextChoices):
        LOW = 'LOW', 'Low'
        MEDIUM = 'MEDIUM', 'Medium'
        HIGH = 'HIGH', 'High'
        CRITICAL = 'CRITICAL', 'Critical'

    class VerificationStatus(models.TextChoices):
        SUPPORTED = 'SUPPORTED', 'Supported by Verified Source'
        CONTRADICTED = 'CONTRADICTED', 'Contradicts Verified Source or Brand Policy'
        UNSUPPORTED = 'UNSUPPORTED', 'Unsupported (Evidence Missing)'
        UNABLE_TO_DETERMINE = 'UNABLE_TO_DETERMINE', 'Unable To Determine (Ambiguous/Stale)'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    review_run = models.ForeignKey(
        ReviewRun, 
        on_delete=models.CASCADE, 
        related_name='findings'
    )
    content_version = models.ForeignKey(
        ContentVersion, 
        on_delete=models.CASCADE, 
        related_name='findings'
    )
    finding_type = models.CharField(
        max_length=32, 
        choices=FindingType.choices, 
        default=FindingType.DETERMINISTIC_RULE
    )
    category = models.CharField(max_length=128)
    flagged_text = models.TextField(help_text="The exact phrase or sentence flagged")
    start_char = models.IntegerField(null=True, blank=True)
    end_char = models.IntegerField(null=True, blank=True)
    severity = models.CharField(
        max_length=16, 
        choices=Severity.choices, 
        default=Severity.MEDIUM
    )
    verification_status = models.CharField(
        max_length=32, 
        choices=VerificationStatus.choices, 
        default=VerificationStatus.UNSUPPORTED
    )
    explanation = models.TextField(help_text="Clear reason why the text was flagged")
    quoted_passage = models.TextField(
        blank=True, 
        help_text="The exact source evidence passage cited"
    )
    source_version = models.ForeignKey(
        SourceDocumentVersion, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='cited_findings'
    )
    source_passage_id = models.CharField(max_length=128, blank=True)
    source_document_code_snapshot = models.CharField(max_length=64, blank=True)
    source_document_title_snapshot = models.CharField(max_length=255, blank=True)
    source_version_label_snapshot = models.CharField(max_length=32, blank=True)
    brand_rule = models.ForeignKey(
        BrandRule, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='rule_findings'
    )
    approved_claim = models.ForeignKey(
        ApprovedClaim, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='claim_findings'
    )
    suggested_correction = models.TextField(
        blank=True, 
        help_text="Recommended replacement copy adhering to brand rules"
    )
    is_citation_validated = models.BooleanField(
        default=False, 
        help_text="True if cited passage was verified against actual stored source records"
    )
    confidence = models.FloatField(null=True, blank=True)
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-severity', 'start_char']
        indexes = [
            models.Index(fields=['content_version', 'severity']),
            models.Index(fields=['content_version', 'verification_status']),
        ]

    def __str__(self):
        return f"[{self.severity}] {self.category}: '{self.flagged_text[:30]}...'"


class Suggestion(models.Model):
    """
    Suggested text improvements linked to a Finding.
    Accepting a suggestion helps the creator construct a revised ContentVersion.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    finding = models.ForeignKey(
        Finding, 
        on_delete=models.CASCADE, 
        related_name='suggestions'
    )
    original_text = models.TextField()
    proposed_text = models.TextField()
    rationale = models.TextField()
    is_accepted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Suggestion for {self.finding.id}: '{self.proposed_text[:30]}...'"


class ReviewComment(models.Model):
    """
    Human collaboration comment attached to a ContentVersion or specific Finding.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content_version = models.ForeignKey(
        ContentVersion, 
        on_delete=models.CASCADE, 
        related_name='comments'
    )
    finding = models.ForeignKey(
        Finding, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='comments'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='review_comments'
    )
    comment_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author.username} @ {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class ApprovalDecision(models.Model):
    """
    Binding governance decision recorded by an authorized Brand Reviewer.
    Applies solely to the exact ContentVersion snapshot.
    """
    class Decision(models.TextChoices):
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
        CHANGES_REQUESTED = 'CHANGES_REQUESTED', 'Changes Requested'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content_version = models.ForeignKey(
        ContentVersion, 
        on_delete=models.CASCADE, 
        related_name='approval_decisions'
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='issued_approvals'
    )
    decision = models.CharField(
        max_length=32, 
        choices=Decision.choices
    )
    decision_notes = models.TextField(blank=True)
    decided_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-decided_at']
        indexes = [
            models.Index(fields=['content_version', 'decision']),
        ]

    def __str__(self):
        return f"{self.decision} by {self.reviewer.username} on v{self.content_version.version_number}"
