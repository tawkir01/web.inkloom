from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    BrandRuleViewSet,
    ApprovedClaimViewSet,
    SourceDocumentViewSet,
    SourceDocumentVersionCreateView,
    BrandAssetViewSet
)

router = DefaultRouter()
router.register(r'rules', BrandRuleViewSet, basename='workspace-rules')
router.register(r'claims', ApprovedClaimViewSet, basename='workspace-claims')
router.register(r'sources', SourceDocumentViewSet, basename='workspace-sources')
router.register(r'assets', BrandAssetViewSet, basename='workspace-assets')

urlpatterns = [
    # Workspaces scoped nested router
    path('workspaces/<uuid:workspace_id>/', include(router.urls)),

    # Direct source version creation
    path('sources/<uuid:source_id>/versions/', SourceDocumentVersionCreateView.as_view(), name='source-version-create'),
]
