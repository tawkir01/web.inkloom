from rest_framework import serializers
from django.db import transaction
from django.contrib.auth import get_user_model
from .models import ContentItem, ContentVersion, ApprovalDecision, ReviewRun, Finding, Suggestion, ReviewComment
from workspaces.serializers import UserProfileSerializer

User = get_user_model()

class ContentVersionSummarySerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    created_by = UserProfileSerializer(read_only=True)
    has_approval = serializers.SerializerMethodField()

    class Meta:
        model = ContentVersion
        fields = [
            'id', 'content_item', 'version_number', 'raw_text',
            'image_file', 'extracted_ocr_text', 'ocr_confidence',
            'status', 'status_display', 'checksum_sha256',
            'created_by', 'created_at', 'has_approval'
        ]
        read_only_fields = ['id', 'content_item', 'version_number', 'status', 'checksum_sha256', 'created_by', 'created_at']

    def get_has_approval(self, obj):
        return obj.status == ContentVersion.Status.APPROVED or obj.approval_decisions.filter(decision=ApprovalDecision.Decision.APPROVED).exists()


class ContentItemSerializer(serializers.ModelSerializer):
    created_by = UserProfileSerializer(read_only=True)
    latest_version = serializers.SerializerMethodField()
    versions_count = serializers.SerializerMethodField()
    versions = ContentVersionSummarySerializer(many=True, read_only=True)

    class Meta:
        model = ContentItem
        fields = [
            'id', 'workspace', 'title', 'description',
            'created_by', 'created_at', 'updated_at',
            'versions_count', 'latest_version', 'versions'
        ]
        read_only_fields = ['id', 'workspace', 'created_by', 'created_at', 'updated_at']

    def get_versions_count(self, obj):
        return obj.versions.count()

    def get_latest_version(self, obj):
        latest = obj.versions.first()
        if latest:
            return ContentVersionSummarySerializer(latest).data
        return None


class ContentItemDetailSerializer(serializers.ModelSerializer):
    created_by = UserProfileSerializer(read_only=True)
    versions = ContentVersionSummarySerializer(many=True, read_only=True)

    class Meta:
        model = ContentItem
        fields = [
            'id', 'workspace', 'title', 'description',
            'created_by', 'created_at', 'updated_at',
            'versions'
        ]
        read_only_fields = ['id', 'workspace', 'created_by', 'created_at', 'updated_at']


class ContentSubmissionCreateSerializer(serializers.Serializer):
    """
    Handles atomic initial submission: creates ContentItem + ContentVersion (v1).
    """
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)
    raw_text = serializers.CharField()
    image_file = serializers.FileField(required=False, allow_null=True)

    def validate_raw_text(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Marketing copy text cannot be empty.")
        return value.strip()


class RevisionCreateSerializer(serializers.Serializer):
    """
    Handles creating a new version (vN+1) from an edited draft.
    Enforces that new revisions start in SUBMITTED state and do NOT inherit prior approvals.
    """
    raw_text = serializers.CharField()
    image_file = serializers.FileField(required=False, allow_null=True)

    def validate_raw_text(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Revised copy text cannot be empty.")
        return value.strip()


class FindingSerializer(serializers.ModelSerializer):
    """
    Serializes a Finding for the review workspace UI.

    What is a Finding?
    ─────────────────
    Every time the rule engine flags a problem in submitted copy, it creates a
    "Finding". This serializer converts that database record into JSON that the
    frontend can display, including:
      - Which exact text was flagged (and where: start_char → end_char)
      - Why it was flagged (explanation)
      - What evidence backs this up (quoted_passage from a source document)
      - Whether it is SUPPORTED / CONTRADICTED / UNSUPPORTED
    """
    finding_type_display = serializers.CharField(source='get_finding_type_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    verification_status_display = serializers.CharField(source='get_verification_status_display', read_only=True)

    # Inline source document details so the UI doesn't need a separate API call
    source_version_label = serializers.SerializerMethodField()
    source_document_code = serializers.SerializerMethodField()
    brand_rule_name = serializers.SerializerMethodField()
    approved_claim_title = serializers.SerializerMethodField()

    class Meta:
        model = Finding
        fields = [
            'id', 'review_run', 'content_version',
            'finding_type', 'finding_type_display',
            'category', 'flagged_text', 'start_char', 'end_char',
            'severity', 'severity_display',
            'verification_status', 'verification_status_display',
            'explanation', 'quoted_passage',
            'source_version', 'source_version_label', 'source_document_code',
            'brand_rule', 'brand_rule_name',
            'approved_claim', 'approved_claim_title',
            'suggested_correction', 'is_citation_validated',
            'confidence', 'is_resolved', 'created_at'
        ]
        read_only_fields = fields

    def get_source_version_label(self, obj):
        return obj.source_version.version_label if obj.source_version else None

    def get_source_document_code(self, obj):
        return obj.source_version.source_document.document_code if obj.source_version else None

    def get_brand_rule_name(self, obj):
        return obj.brand_rule.name if obj.brand_rule else None

    def get_approved_claim_title(self, obj):
        return obj.approved_claim.claim_title if obj.approved_claim else None


class ReviewRunSerializer(serializers.ModelSerializer):
    """
    Serializes a ReviewRun along with all its Findings.

    What is a ReviewRun?
    ─────────────────────
    When a user clicks "Run AI Review" in the dashboard, the backend:
      1. Creates a ReviewRun record (like an audit log of this analysis session)
      2. Runs the rule engine
      3. Saves each Finding under this ReviewRun
      4. Returns this serialized record back to the frontend
    """
    findings = FindingSerializer(many=True, read_only=True)
    triggered_by_username = serializers.SerializerMethodField()
    run_status_display = serializers.CharField(source='get_run_status_display', read_only=True)
    findings_count = serializers.SerializerMethodField()
    critical_count = serializers.SerializerMethodField()
    high_count = serializers.SerializerMethodField()

    class Meta:
        model = ReviewRun
        fields = [
            'id', 'content_version', 'triggered_by', 'triggered_by_username',
            'run_status', 'run_status_display', 'ai_provider',
            'rules_checked_count', 'sources_consulted_count',
            'findings', 'findings_count', 'critical_count', 'high_count',
            'error_message', 'created_at'
        ]
        read_only_fields = fields

    def get_triggered_by_username(self, obj):
        return obj.triggered_by.username if obj.triggered_by else None

    def get_findings_count(self, obj):
        return obj.findings.count()

    def get_critical_count(self, obj):
        return obj.findings.filter(severity='CRITICAL').count()

    def get_high_count(self, obj):
        return obj.findings.filter(severity='HIGH').count()


class ApprovalDecisionSerializer(serializers.ModelSerializer):
    """
    Serializes an ApprovalDecision — the binding human governance decision.

    Important security note for beginners:
    ───────────────────────────────────────
    Approval decisions are PERMANENTLY BOUND to a specific ContentVersion.
    If the creator submits a new revision (v2, v3...), this approval does NOT
    carry over. The reviewer must approve each version independently.
    This is enforced at the model level (FK → ContentVersion, not ContentItem).
    """
    reviewer_username = serializers.SerializerMethodField()
    decision_display = serializers.CharField(source='get_decision_display', read_only=True)

    class Meta:
        model = ApprovalDecision
        fields = [
            'id', 'content_version', 'reviewer', 'reviewer_username',
            'decision', 'decision_display', 'decision_notes', 'decided_at'
        ]
        read_only_fields = ['id', 'reviewer', 'reviewer_username', 'decided_at']

    def get_reviewer_username(self, obj):
        return obj.reviewer.username


class ApprovalDecisionCreateSerializer(serializers.Serializer):
    """
    Validates incoming data when a Brand Reviewer submits an approval decision.
    Separate from the read serializer to enforce input constraints cleanly.
    """
    decision = serializers.ChoiceField(choices=ApprovalDecision.Decision.choices)
    decision_notes = serializers.CharField(required=False, allow_blank=True)


class ReviewCommentSerializer(serializers.ModelSerializer):
    """
    Serializes human collaboration comments on a ContentVersion or specific Finding.
    """
    author_username = serializers.SerializerMethodField()

    class Meta:
        model = ReviewComment
        fields = [
            'id', 'content_version', 'finding', 'author', 'author_username',
            'comment_text', 'created_at'
        ]
        read_only_fields = ['id', 'author', 'author_username', 'created_at']

    def get_author_username(self, obj):
        return obj.author.username


class ReviewCommentCreateSerializer(serializers.Serializer):
    """
    Validates incoming comment data.
    """
    comment_text = serializers.CharField(min_length=1)
    finding_id = serializers.UUIDField(required=False, allow_null=True)
