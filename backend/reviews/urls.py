from django.urls import path
from .views import (
    WorkspaceContentListView,
    ContentItemDetailView,
    ContentRevisionCreateView,
    ContentVersionDetailView,
    # Phase 6: Review runs, approval, comments
    ReviewRunCreateView,
    ReviewRunListView,
    ApprovalDecisionView,
    ReviewCommentListView,
)

urlpatterns = [
    # ─────────────────────────────────────────────
    # Content submission & listing per workspace
    # ─────────────────────────────────────────────
    path(
        'workspaces/<uuid:workspace_id>/content/',
        WorkspaceContentListView.as_view(),
        name='workspace-content-list'
    ),

    # ─────────────────────────────────────────────
    # Content item detail & full version lineage
    # ─────────────────────────────────────────────
    path(
        'content/<uuid:content_id>/',
        ContentItemDetailView.as_view(),
        name='content-item-detail'
    ),

    # ─────────────────────────────────────────────
    # Content revision creation (POST new version)
    # ─────────────────────────────────────────────
    path(
        'content/<uuid:content_id>/versions/',
        ContentRevisionCreateView.as_view(),
        name='content-revision-create'
    ),

    # ─────────────────────────────────────────────
    # Exact immutable version snapshot detail
    # ─────────────────────────────────────────────
    path(
        'content/<uuid:content_id>/versions/<int:version_number>/',
        ContentVersionDetailView.as_view(),
        name='content-version-detail'
    ),

    # ─────────────────────────────────────────────
    # PHASE 6: Trigger / List Review Runs
    # POST → triggers the rule engine on this version
    # GET  → lists all prior review runs for this version
    # ─────────────────────────────────────────────
    path(
        'content/<uuid:content_id>/versions/<int:version_number>/review/',
        ReviewRunCreateView.as_view(),
        name='review-run-create'
    ),
    path(
        'content/<uuid:content_id>/versions/<int:version_number>/reviews/',
        ReviewRunListView.as_view(),
        name='review-run-list'
    ),

    # ─────────────────────────────────────────────
    # PHASE 6: Approval Decisions
    # POST → Brand Reviewer submits a decision
    # GET  → List all decisions for this version
    # ─────────────────────────────────────────────
    path(
        'content/<uuid:content_id>/versions/<int:version_number>/approval/',
        ApprovalDecisionView.as_view(),
        name='approval-decision'
    ),

    # ─────────────────────────────────────────────
    # PHASE 6: Review Comments
    # POST → Add a comment (optionally on a specific Finding)
    # GET  → List all comments for this version
    # ─────────────────────────────────────────────
    path(
        'content/<uuid:content_id>/versions/<int:version_number>/comments/',
        ReviewCommentListView.as_view(),
        name='review-comments'
    ),
]
