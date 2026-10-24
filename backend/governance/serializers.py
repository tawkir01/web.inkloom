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
    class Meta:
        model = ApprovedClaim
        fields = [
            'id', 'workspace', 'claim_title', 'permitted_statement',
            'required_qualifiers', 'disallowed_variations', 'category',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'workspace', 'created_at', 'updated_at']


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
        for item in value:
            if not isinstance(item, dict) or 'text' not in item:
                raise serializers.ValidationError("Each excerpt must be an object with at least a 'text' field.")
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
