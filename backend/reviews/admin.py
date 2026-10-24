from django.contrib import admin
from .models import ContentItem, ContentVersion, ReviewRun, Finding, Suggestion, ReviewComment, ApprovalDecision

class ContentVersionInline(admin.TabularInline):
    model = ContentVersion
    extra = 0
    readonly_fields = ('version_number', 'checksum_sha256', 'created_by', 'created_at')

@admin.register(ContentItem)
class ContentItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'workspace', 'created_by', 'updated_at')
    list_filter = ('workspace',)
    search_fields = ('title', 'description', 'created_by__username')
    inlines = [ContentVersionInline]

@admin.register(ContentVersion)
class ContentVersionAdmin(admin.ModelAdmin):
    list_display = ('content_item', 'version_number', 'status', 'created_by', 'checksum_sha256', 'created_at')
    list_filter = ('status', 'content_item__workspace')
    search_fields = ('content_item__title', 'raw_text')
    readonly_fields = ('checksum_sha256', 'created_at')

@admin.register(ReviewRun)
class ReviewRunAdmin(admin.ModelAdmin):
    list_display = ('id', 'content_version', 'run_status', 'ai_provider', 'rules_checked_count', 'created_at')
    list_filter = ('run_status', 'ai_provider')
    search_fields = ('content_version__content_item__title',)

@admin.register(Finding)
class FindingAdmin(admin.ModelAdmin):
    list_display = ('category', 'content_version', 'severity', 'verification_status', 'is_citation_validated', 'is_resolved')
    list_filter = ('severity', 'verification_status', 'is_citation_validated', 'is_resolved')
    search_fields = ('flagged_text', 'explanation', 'quoted_passage')

@admin.register(Suggestion)
class SuggestionAdmin(admin.ModelAdmin):
    list_display = ('finding', 'is_accepted', 'created_at')
    list_filter = ('is_accepted',)
    search_fields = ('original_text', 'proposed_text')

@admin.register(ReviewComment)
class ReviewCommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'content_version', 'created_at')
    search_fields = ('comment_text', 'author__username')

@admin.register(ApprovalDecision)
class ApprovalDecisionAdmin(admin.ModelAdmin):
    list_display = ('content_version', 'reviewer', 'decision', 'decided_at')
    list_filter = ('decision',)
    search_fields = ('content_version__content_item__title', 'reviewer__username', 'decision_notes')
