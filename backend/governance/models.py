import uuid
from django.db import models
from workspaces.models import ClientWorkspace

class BrandRule(models.Model):
    """
    Brand rules configurable per workspace.
    Covers exact prohibited phrases, mandatory terminology, disclaimers, and qualifiers.
    """
    class RuleType(models.TextChoices):
        PROHIBITED_PHRASE = 'PROHIBITED_PHRASE', 'Prohibited Phrase'
        REQUIRED_TERM = 'REQUIRED_TERM', 'Required Terminology'
        REQUIRED_QUALIFIER = 'REQUIRED_QUALIFIER', 'Required Qualifier'
        DISALLOWED_CLAIM = 'DISALLOWED_CLAIM', 'Disallowed Claim Wording'
        TONE_GUIDANCE = 'TONE_GUIDANCE', 'Tone Guidance'

    class Severity(models.TextChoices):
        LOW = 'LOW', 'Low'
        MEDIUM = 'MEDIUM', 'Medium'
        HIGH = 'HIGH', 'High'
        CRITICAL = 'CRITICAL', 'Critical'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(
        ClientWorkspace, 
        on_delete=models.CASCADE, 
        related_name='brand_rules'
    )
    name = models.CharField(max_length=255)
    rule_type = models.CharField(
        max_length=32, 
        choices=RuleType.choices, 
        default=RuleType.PROHIBITED_PHRASE
    )
    pattern_or_phrase = models.TextField(
        help_text="Target phrase or regex pattern to identify in submitted copy"
    )
    preferred_alternative = models.TextField(
        blank=True, 
        help_text="Approved replacement phrasing or required qualifier"
    )
    explanation = models.TextField(
        help_text="Explanation shown to creators why this rule was triggered"
    )
    severity = models.CharField(
        max_length=16, 
        choices=Severity.choices, 
        default=Severity.HIGH
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-severity', 'name']
        indexes = [
            models.Index(fields=['workspace', 'rule_type']),
            models.Index(fields=['workspace', 'is_active']),
        ]

    def __str__(self):
        return f"[{self.get_severity_display()}] {self.name} ({self.workspace.name})"


class ApprovedClaim(models.Model):
    """
    Registered product and marketing claims vetted by legal/brand teams.
    Defines exact permitted wording, required qualifiers, and banned variations.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(
        ClientWorkspace, 
        on_delete=models.CASCADE, 
        related_name='approved_claims'
    )
    claim_title = models.CharField(max_length=255)
    permitted_statement = models.TextField(
        help_text="The exact factual statement approved for marketing copy"
    )
    required_qualifiers = models.TextField(
        blank=True,
        help_text="Mandatory conditions or footnotes (e.g. 'up to 20%', 'in lab conditions')"
    )
    disallowed_variations = models.TextField(
        blank=True,
        help_text="Common exaggerated variations that violate this claim"
    )
    source_version = models.ForeignKey(
        'SourceDocumentVersion',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_claims',
        help_text="Approved source document version supporting this claim"
    )
    category = models.CharField(max_length=100, default='General')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'claim_title']
        indexes = [
            models.Index(fields=['workspace', 'category']),
            models.Index(fields=['workspace', 'is_active']),
        ]

    def __str__(self):
        return f"{self.claim_title} ({self.workspace.name})"


class SourceDocument(models.Model):
    """
    Catalog of evidentiary source records (scientific studies, trial reports, legal disclaimers).
    Provides parent record for versioned evidence passages.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(
        ClientWorkspace, 
        on_delete=models.CASCADE, 
        related_name='source_documents'
    )
    title = models.CharField(max_length=255)
    document_code = models.CharField(
        max_length=64, 
        help_text="Unique identifier like SRC-ECO-2025-01"
    )
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('workspace', 'document_code')
        indexes = [
            models.Index(fields=['workspace', 'document_code']),
        ]

    def __str__(self):
        return f"{self.document_code}: {self.title} ({self.workspace.name})"


class SourceDocumentVersion(models.Model):
    """
    An immutable version of an approved source document.
    Captures effective/expiration dates and stored passages.
    When a review runs, it links to this exact version.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source_document = models.ForeignKey(
        SourceDocument, 
        on_delete=models.PROTECT,
        related_name='versions'
    )
    version_label = models.CharField(max_length=32, default='v1.0')
    full_text_content = models.TextField(help_text="Complete reference text")
    passage_excerpts = models.JSONField(
        default=list, 
        help_text="Structured passages [{ 'passage_id': 'P1', 'text': '...' }]"
    )
    effective_date = models.DateField(null=True, blank=True)
    expiration_date = models.DateField(null=True, blank=True)
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('source_document', 'version_label')
        ordering = ['-created_at']

    def is_currently_valid(self):
        """Returns True if document is approved and not expired."""
        from django.utils import timezone
        today = timezone.now().date()
        if not self.is_approved:
            return False
        if self.effective_date and today < self.effective_date:
            return False
        if self.expiration_date and today > self.expiration_date:
            return False
        return True

    def __str__(self):
        return f"{self.source_document.document_code} [{self.version_label}]"


class BrandAsset(models.Model):
    """
    Visual and media guidelines (approved logos, product renders, packaging designs).
    """
    class AssetType(models.TextChoices):
        LOGO = 'LOGO', 'Logo'
        PACKAGING = 'PACKAGING', 'Packaging'
        PRODUCT_PHOTO = 'PRODUCT_PHOTO', 'Product Photo'
        BADGE = 'CERTIFICATION_BADGE', 'Certification Badge'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(
        ClientWorkspace, 
        on_delete=models.CASCADE, 
        related_name='brand_assets'
    )
    asset_name = models.CharField(max_length=255)
    asset_type = models.CharField(
        max_length=32, 
        choices=AssetType.choices, 
        default=AssetType.LOGO
    )
    file = models.FileField(upload_to='brand_assets/', blank=True, null=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['asset_name']

    def __str__(self):
        return f"{self.asset_name} ({self.get_asset_type_display()}) - {self.workspace.name}"
