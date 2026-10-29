from django.contrib import admin
from .models import BrandRule, ApprovedClaim, SourceDocument, SourceDocumentVersion, BrandAsset

@admin.register(BrandRule)
class BrandRuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'workspace', 'rule_type', 'severity', 'is_active', 'created_at')
    list_filter = ('rule_type', 'severity', 'is_active', 'workspace')
    search_fields = ('name', 'pattern_or_phrase', 'explanation')

@admin.register(ApprovedClaim)
class ApprovedClaimAdmin(admin.ModelAdmin):
    list_display = ('claim_title', 'workspace', 'category', 'is_active', 'created_at')
    list_filter = ('category', 'is_active', 'workspace')
    search_fields = ('claim_title', 'permitted_statement', 'required_qualifiers')

class SourceDocumentVersionInline(admin.TabularInline):
    model = SourceDocumentVersion
    extra = 0
    can_delete = False
    readonly_fields = (
        'version_label',
        'full_text_content',
        'passage_excerpts',
        'effective_date',
        'expiration_date',
        'is_approved',
        'created_at',
    )

    def has_add_permission(self, request, obj=None):
        return False

@admin.register(SourceDocument)
class SourceDocumentAdmin(admin.ModelAdmin):
    list_display = ('document_code', 'title', 'workspace', 'created_at')
    list_filter = ('workspace',)
    search_fields = ('document_code', 'title', 'description')
    inlines = [SourceDocumentVersionInline]

    def get_readonly_fields(self, request, obj=None):
        return ('workspace',) if obj else ()

@admin.register(SourceDocumentVersion)
class SourceDocumentVersionAdmin(admin.ModelAdmin):
    list_display = ('source_document', 'version_label', 'effective_date', 'expiration_date', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'source_document__workspace')
    search_fields = ('source_document__document_code', 'version_label', 'full_text_content')

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return (
                'source_document',
                'version_label',
                'full_text_content',
                'passage_excerpts',
                'effective_date',
                'expiration_date',
                'is_approved',
                'created_at',
            )
        return ()

    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(BrandAsset)
class BrandAssetAdmin(admin.ModelAdmin):
    list_display = ('asset_name', 'workspace', 'asset_type', 'is_active', 'created_at')
    list_filter = ('asset_type', 'is_active', 'workspace')
    search_fields = ('asset_name', 'description')
