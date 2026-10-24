"""
URL configuration for inkloom_backend project.
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from workspaces.models import ClientWorkspace, Organisation
from governance.models import BrandRule, ApprovedClaim, SourceDocument
from reviews.models import ContentItem, ContentVersion
from audit_log.models import AuditEvent
from django.contrib.auth import get_user_model

User = get_user_model()

def health_check(request):
    """
    Health check endpoint for platform verification.
    """
    return JsonResponse({
        "status": "healthy",
        "app": "Inkloom Guardian",
        "version": "1.0.0-phase2",
        "message": "AI-Powered Brand Governance & Content Trust Platform API is operational."
    })

def system_stats(request):
    """
    Returns real database statistics across the 17 governance models.
    """
    workspaces = ClientWorkspace.objects.filter(is_active=True).values('id', 'name', 'slug', 'industry')
    return JsonResponse({
        "organisations_count": Organisation.objects.count(),
        "workspaces_count": ClientWorkspace.objects.count(),
        "workspaces": list(workspaces),
        "brand_rules_count": BrandRule.objects.count(),
        "approved_claims_count": ApprovedClaim.objects.count(),
        "source_documents_count": SourceDocument.objects.count(),
        "users_count": User.objects.count(),
        "content_items_count": ContentItem.objects.count(),
        "audit_events_count": AuditEvent.objects.count(),
    })

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', health_check, name='api-health'),
    path('api/stats/', system_stats, name='api-stats'),
    path('api/', include('workspaces.urls')),
    path('api/', include('governance.urls')),
    path('api/', include('reviews.urls')),
]
