from rest_framework import serializers
from .models import BrandRule, ApprovedClaim, SourceDocument, SourceDocumentVersion, BrandAsset

class BrandRuleSerializer(serializers.ModelSerializer):
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    rule_type_display = serializers.CharField(source='get_rule_type_display', read_only=True)

    class Meta:
        model = BrandRule
        fields = [
            'id', 'workspace', 'name', 'rule_type', 'rule_type_display',
            'pattern_or_phrase', 'preferred_alternative', 'explanation',
            'severity', 'severity_display', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'workspace', 'created_at', 'updated_at']


class ApprovedClaimSerializer(serializers.ModelSerializer):
    source_document_code = serializers.SerializerMethodField()
    source_document_title = serializers.SerializerMethodField()
    source_version_label = serializers.SerializerMethodField()

    class Meta:
        model = ApprovedClaim
        fields = [
            'id', 'workspace', 'claim_title', 'permitted_statement',
            'required_qualifiers', 'disallowed_variations', 'category',
            'source_version', 'source_document_code', 'source_document_title',
            'source_version_label', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'workspace', 'created_at', 'updated_at']

    def validate(self, attrs):
        source_version = attrs.get(
            'source_version',
            self.instance.source_version if self.instance else None
        )
        view = self.context.get('view')
        if source_version and view and hasattr(view, 'get_workspace'):
            if source_version.source_document.workspace_id != view.get_workspace().id:
                raise serializers.ValidationError({
                    'source_version': 'The evidence source must belong to this workspace.'
                })
        return attrs

    def get_source_document_code(self, obj):
        if obj.source_version_id:
            return obj.source_version.source_document.document_code
        return None

    def get_source_document_title(self, obj):
        if obj.source_version_id:
            return obj.source_version.source_document.title
        return None

    def get_source_version_label(self, obj):
        return obj.source_version.version_label if obj.source_version_id else None


class SourceDocumentVersionSerializer(serializers.ModelSerializer):
    is_currently_valid = serializers.BooleanField(read_only=True)

    class Meta:
        model = SourceDocumentVersion
        fields = [
            'id', 'source_document', 'version_label', 'full_text_content',
            'passage_excerpts', 'effective_date', 'expiration_date',
            'is_approved', 'is_currently_valid', 'created_at'
        ]
        read_only_fields = ['id', 'source_document', 'created_at']

    def validate_passage_excerpts(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Passage excerpts must be a list of passage objects.")
        passage_ids = set()
        for item in value:
            if not isinstance(item, dict):
                raise serializers.ValidationError("Each excerpt must be an object.")
            passage_id = item.get('passage_id')
            passage_text = item.get('text')
            if not isinstance(passage_id, str) or not passage_id.strip():
                raise serializers.ValidationError("Each excerpt needs a non-empty passage_id.")
            if len(passage_id) > 128:
                raise serializers.ValidationError("Passage IDs must be 128 characters or fewer.")
            if passage_id in passage_ids:
                raise serializers.ValidationError("Passage IDs must be unique within a source version.")
            if not isinstance(passage_text, str) or not passage_text.strip():
                raise serializers.ValidationError("Each excerpt needs non-empty text.")
            passage_ids.add(passage_id)
        return value


class SourceDocumentSerializer(serializers.ModelSerializer):
    versions = SourceDocumentVersionSerializer(many=True, read_only=True)
    latest_version = serializers.SerializerMethodField()

    class Meta:
        model = SourceDocument
        fields = [
            'id', 'workspace', 'document_code', 'title', 'description',
            'versions', 'latest_version', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'workspace', 'created_at', 'updated_at']

    def get_latest_version(self, obj):
        latest = obj.versions.first()
        if latest:
            return SourceDocumentVersionSerializer(latest).data
        return None


class BrandAssetSerializer(serializers.ModelSerializer):
    asset_type_display = serializers.CharField(source='get_asset_type_display', read_only=True)

    class Meta:
        model = BrandAsset
        fields = [
            'id', 'workspace', 'asset_name', 'asset_type', 'asset_type_display',
            'file', 'description', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'workspace', 'created_at']
