from rest_framework import views, status, permissions
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction
from workspaces.models import ClientWorkspace, WorkspaceMembership
from workspaces.permissions import IsWorkspaceMember, IsContentCreator, IsBrandReviewer
from governance.models import BrandRule, ApprovedClaim, SourceDocumentVersion
from .models import ContentItem, ContentVersion, ApprovalDecision, ReviewRun, Finding, ReviewComment
from .serializers import (
    ContentItemSerializer,
    ContentItemDetailSerializer,
    ContentVersionSummarySerializer,
    ContentSubmissionCreateSerializer,
    RevisionCreateSerializer,
    ReviewRunSerializer,
    FindingSerializer,
    ApprovalDecisionSerializer,
    ApprovalDecisionCreateSerializer,
    ReviewCommentSerializer,
    ReviewCommentCreateSerializer,
)
from .rule_engine import run_full_review
from audit_log.models import AuditEvent

class WorkspaceContentListView(views.APIView):
    """
    GET: Lists all content items for a workspace.
    POST: Submits new marketing copy/media, creating ContentItem and ContentVersion (v1).
    """
    permission_classes = [permissions.IsAuthenticated, IsWorkspaceMember]

    def get_workspace(self, workspace_id):
        return get_object_or_404(ClientWorkspace, id=workspace_id, is_active=True)

    def get(self, request, workspace_id):
        workspace = self.get_workspace(workspace_id)
        self.check_object_permissions(request, workspace)

        items = ContentItem.objects.filter(workspace=workspace).prefetch_related('versions')
        serializer = ContentItemSerializer(items, many=True)
        return Response(serializer.data)

    def post(self, request, workspace_id):
        workspace = self.get_workspace(workspace_id)
        self.check_object_permissions(request, workspace)

        # Enforce that user is a Content Creator or Admin in this workspace
        if not WorkspaceMembership.objects.filter(
            workspace=workspace,
            user=request.user,
            role__in=[WorkspaceMembership.Role.CREATOR, WorkspaceMembership.Role.ADMIN],
            is_active=True
        ).exists() and not request.user.is_superuser:
            return Response(
                {"detail": "Content Creator role required in this workspace to submit content."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = ContentSubmissionCreateSerializer(data=request.data)
        if serializer.is_valid():
            with transaction.atomic():
                item = ContentItem.objects.create(
                    workspace=workspace,
                    title=serializer.validated_data['title'],
                    description=serializer.validated_data.get('description', ''),
                    created_by=request.user
                )

                version = ContentVersion.objects.create(
                    content_item=item,
                    version_number=1,
                    raw_text=serializer.validated_data['raw_text'],
                    image_file=serializer.validated_data.get('image_file'),
                    status=ContentVersion.Status.SUBMITTED,
                    created_by=request.user
                )

                AuditEvent.objects.create(
                    workspace=workspace,
                    user=request.user,
                    event_type=AuditEvent.EventType.CONTENT_SUBMITTED,
                    description=f"New content '{item.title}' submitted (v1 created).",
                    metadata={"content_id": str(item.id), "version_id": str(version.id)}
                )

            return Response(ContentItemDetailSerializer(item).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ContentItemDetailView(views.APIView):
    """
    GET: Retrieves ContentItem along with its full immutable version lineage.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, content_id):
        item = get_object_or_404(ContentItem, id=content_id)

        # Enforce workspace membership
        if not WorkspaceMembership.objects.filter(
            workspace=item.workspace,
            user=request.user,
            is_active=True
        ).exists() and not request.user.is_superuser:
            return Response(
                {"detail": "You do not have access to this workspace's content items."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = ContentItemDetailSerializer(item)
        return Response(serializer.data)


class ContentRevisionCreateView(views.APIView):
    """
    POST: Spawns a new sequential immutable ContentVersion (vN+1) from edited copy.
    Critical compliance guarantee: A new revision resets status to SUBMITTED and
    NEVER inherits approval from prior versions.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, content_id):
        item = get_object_or_404(ContentItem, id=content_id)

        # Enforce Creator or Admin role
        if not WorkspaceMembership.objects.filter(
            workspace=item.workspace,
            user=request.user,
            role__in=[WorkspaceMembership.Role.CREATOR, WorkspaceMembership.Role.ADMIN],
            is_active=True
        ).exists() and not request.user.is_superuser:
            return Response(
                {"detail": "Content Creator role required in this workspace to submit revisions."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = RevisionCreateSerializer(data=request.data)
        if serializer.is_valid():
            with transaction.atomic():
                highest_version = item.versions.order_by('-version_number').first()
                next_version_num = (highest_version.version_number + 1) if highest_version else 1

                new_version = ContentVersion.objects.create(
                    content_item=item,
                    version_number=next_version_num,
                    raw_text=serializer.validated_data['raw_text'],
                    image_file=serializer.validated_data.get('image_file'),
                    status=ContentVersion.Status.SUBMITTED,
                    created_by=request.user
                )

                AuditEvent.objects.create(
                    workspace=item.workspace,
                    user=request.user,
                    event_type=AuditEvent.EventType.CONTENT_REVISED,
                    description=f"Content '{item.title}' revised: spawned version v{new_version.version_number}.",
                    metadata={"content_id": str(item.id), "version_id": str(new_version.id), "version": next_version_num}
                )

            return Response(ContentVersionSummarySerializer(new_version).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ContentVersionDetailView(views.APIView):
    """
    GET: Retrieves an exact immutable ContentVersion snapshot.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, content_id, version_number):
        item = get_object_or_404(ContentItem, id=content_id)

        # Enforce workspace membership
        if not WorkspaceMembership.objects.filter(
            workspace=item.workspace,
            user=request.user,
            is_active=True
        ).exists() and not request.user.is_superuser:
            return Response(
                {"detail": "You do not have access to this workspace's content items."},
                status=status.HTTP_403_FORBIDDEN
            )

        version = get_object_or_404(ContentVersion, content_item=item, version_number=version_number)
        serializer = ContentVersionSummarySerializer(version)
        return Response(serializer.data)


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 6: Review Run — Rule Engine Integration
# ─────────────────────────────────────────────────────────────────────────────

class ReviewRunCreateView(views.APIView):
    """
    POST /api/content/<content_id>/versions/<version_number>/review/
    Triggers the deterministic brand governance rule engine on a specific
    immutable ContentVersion snapshot.

    What happens when you call this endpoint?
    ─────────────────────────────────────────
    1. The API verifies the user is a member of the correct workspace.
    2. Creates a ReviewRun record (status=RUNNING) to track this analysis session.
    3. Calls run_full_review() from rule_engine.py which:
        a. Checks the text against all active BrandRule records (prohibited phrases,
           required terms, tone guidance)
        b. Verifies factual claims against ApprovedClaim records
        c. Cross-references with SourceDocumentVersion passages
    4. Saves all RawFinding objects returned by the engine as Finding DB records.
    5. Updates the ContentVersion status to NEEDS_CHANGES or READY_FOR_REVIEW.
    6. Marks the ReviewRun as COMPLETED and returns the full result.

    Everything is wrapped in a database transaction — if anything fails midway,
    nothing is partially saved.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, content_id, version_number):
        item = get_object_or_404(ContentItem, id=content_id)
        workspace = item.workspace

        # Verify workspace membership
        if not WorkspaceMembership.objects.filter(
            workspace=workspace,
            user=request.user,
            is_active=True
        ).exists() and not request.user.is_superuser:
            return Response(
                {"detail": "You must be a workspace member to trigger a review."},
                status=status.HTTP_403_FORBIDDEN
            )

        version = get_object_or_404(
            ContentVersion,
            content_item=item,
            version_number=version_number
        )

        # Don't re-run if already approved or processing
        if version.status == ContentVersion.Status.APPROVED:
            return Response(
                {"detail": "This version is already approved. Create a new revision to re-review."},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            # Step 1: Create a ReviewRun record to track this session
            review_run = ReviewRun.objects.create(
                content_version=version,
                triggered_by=request.user,
                run_status=ReviewRun.RunStatus.RUNNING,
                ai_provider='inkloom_deterministic_v1',
            )

            # Update content version status to PROCESSING
            version.status = ContentVersion.Status.PROCESSING
            version.save(update_fields=['status'])

            try:
                # Step 2: Run the deterministic rule engine
                engine_result = run_full_review(version, workspace)

                # Step 3: Persist all findings to the database
                db_findings = []
                for raw in engine_result.findings:
                    # Look up the related DB objects from the IDs in RawFinding
                    brand_rule = None
                    if raw.brand_rule_id:
                        brand_rule = BrandRule.objects.filter(id=raw.brand_rule_id).first()

                    approved_claim = None
                    if raw.approved_claim_id:
                        approved_claim = ApprovedClaim.objects.filter(id=raw.approved_claim_id).first()

                    source_version = None
                    if raw.source_version_id:
                        source_version = SourceDocumentVersion.objects.filter(id=raw.source_version_id).first()

                    f = Finding.objects.create(
                        review_run=review_run,
                        content_version=version,
                        finding_type=raw.finding_type,
                        category=raw.category,
                        flagged_text=raw.flagged_text,
                        start_char=raw.start_char,
                        end_char=raw.end_char,
                        severity=raw.severity,
                        verification_status=raw.verification_status,
                        explanation=raw.explanation,
                        quoted_passage=raw.quoted_passage,
                        brand_rule=brand_rule,
                        approved_claim=approved_claim,
                        source_version=source_version,
                        suggested_correction=raw.suggested_correction,
                        confidence=raw.confidence,
                        is_citation_validated=raw.is_citation_validated,
                    )
                    db_findings.append(f)

                # Step 4: Update ReviewRun with summary statistics
                review_run.run_status = ReviewRun.RunStatus.COMPLETED
                review_run.rules_checked_count = engine_result.rules_checked_count
                review_run.sources_consulted_count = engine_result.sources_consulted_count
                review_run.save()

                # Step 5: Update ContentVersion status based on findings
                # If any CRITICAL or HIGH severity issues found → NEEDS_CHANGES
                # Otherwise → READY_FOR_REVIEW
                has_blocking_issues = any(
                    f.severity in (Finding.Severity.CRITICAL, Finding.Severity.HIGH)
                    and f.verification_status in (
                        Finding.VerificationStatus.CONTRADICTED,
                        Finding.VerificationStatus.UNSUPPORTED
                    )
                    for f in db_findings
                )
                version.status = (
                    ContentVersion.Status.NEEDS_CHANGES
                    if has_blocking_issues
                    else ContentVersion.Status.READY_FOR_REVIEW
                )
                version.save(update_fields=['status'])

                # Step 6: Audit log entry
                AuditEvent.objects.create(
                    workspace=workspace,
                    user=request.user,
                    event_type=AuditEvent.EventType.REVIEW_RUN_COMPLETED,
                    description=(
                        f"Review run completed for '{item.title}' v{version_number}. "
                        f"{len(db_findings)} findings. "
                        f"Rules checked: {engine_result.rules_checked_count}. "
                        f"Sources consulted: {engine_result.sources_consulted_count}."
                    ),
                    metadata={
                        "review_run_id": str(review_run.id),
                        "findings_count": len(db_findings),
                        "new_status": version.status,
                    }
                )

            except Exception as e:
                # If the engine crashes, mark the run as FAILED (don't silently swallow)
                review_run.run_status = ReviewRun.RunStatus.FAILED
                review_run.error_message = str(e)
                review_run.save()
                version.status = ContentVersion.Status.FAILED
                version.save(update_fields=['status'])
                return Response(
                    {"detail": f"Review engine failed: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        serializer = ReviewRunSerializer(review_run)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ReviewRunListView(views.APIView):
    """
    GET /api/content/<content_id>/versions/<version_number>/reviews/
    Lists all past ReviewRun records for a specific ContentVersion.
    Allows the UI to show review history without re-running.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, content_id, version_number):
        item = get_object_or_404(ContentItem, id=content_id)

        if not WorkspaceMembership.objects.filter(
            workspace=item.workspace,
            user=request.user,
            is_active=True
        ).exists() and not request.user.is_superuser:
            return Response({"detail": "Access denied."}, status=status.HTTP_403_FORBIDDEN)

        version = get_object_or_404(ContentVersion, content_item=item, version_number=version_number)
        runs = ReviewRun.objects.filter(content_version=version).prefetch_related('findings')
        serializer = ReviewRunSerializer(runs, many=True)
        return Response(serializer.data)


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 6: Approval Workflow — Human Governance Decisions
# ─────────────────────────────────────────────────────────────────────────────

class ApprovalDecisionView(views.APIView):
    """
    GET  /api/content/<content_id>/versions/<version_number>/approval/
         → Returns all approval decisions for this version

    POST /api/content/<content_id>/versions/<version_number>/approval/
         → Brand Reviewer submits an APPROVED / REJECTED / CHANGES_REQUESTED decision

    Security Guarantee:
    ───────────────────
    Only users with the BRAND_REVIEWER or ADMIN role in this workspace can
    make approval decisions. Content Creators cannot approve their own work.
    Each decision is bound to the exact ContentVersion — newer revisions require
    fresh approval from scratch.
    """
    permission_classes = [permissions.IsAuthenticated]

    def _get_version_and_check_access(self, request, content_id, version_number):
        item = get_object_or_404(ContentItem, id=content_id)
        if not WorkspaceMembership.objects.filter(
            workspace=item.workspace,
            user=request.user,
            is_active=True
        ).exists() and not request.user.is_superuser:
            return None, None, Response({"detail": "Access denied."}, status=status.HTTP_403_FORBIDDEN)
        version = get_object_or_404(ContentVersion, content_item=item, version_number=version_number)
        return item, version, None

    def get(self, request, content_id, version_number):
        item, version, error = self._get_version_and_check_access(request, content_id, version_number)
        if error:
            return error

        decisions = ApprovalDecision.objects.filter(content_version=version)
        serializer = ApprovalDecisionSerializer(decisions, many=True)
        return Response(serializer.data)

    def post(self, request, content_id, version_number):
        item, version, error = self._get_version_and_check_access(request, content_id, version_number)
        if error:
            return error

        workspace = item.workspace

        # Enforce REVIEWER or ADMIN role — Creators cannot approve their own copy
        is_reviewer_or_admin = WorkspaceMembership.objects.filter(
            workspace=workspace,
            user=request.user,
            role__in=[WorkspaceMembership.Role.REVIEWER, WorkspaceMembership.Role.ADMIN],
            is_active=True
        ).exists()

        if not is_reviewer_or_admin and not request.user.is_superuser:
            return Response(
                {"detail": "Brand Reviewer or Admin role required to make approval decisions."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Reject if the version hasn't been reviewed yet
        if version.status not in (
            ContentVersion.Status.READY_FOR_REVIEW,
            ContentVersion.Status.NEEDS_CHANGES,
            ContentVersion.Status.SUBMITTED
        ):
            return Response(
                {"detail": f"Cannot decide on a version with status '{version.status}'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        input_serializer = ApprovalDecisionCreateSerializer(data=request.data)
        if not input_serializer.is_valid():
            return Response(input_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            decision = ApprovalDecision.objects.create(
                content_version=version,
                reviewer=request.user,
                decision=input_serializer.validated_data['decision'],
                decision_notes=input_serializer.validated_data.get('decision_notes', ''),
            )

            # Map the decision to a ContentVersion status update
            decision_to_status = {
                ApprovalDecision.Decision.APPROVED: ContentVersion.Status.APPROVED,
                ApprovalDecision.Decision.REJECTED: ContentVersion.Status.REJECTED,
                ApprovalDecision.Decision.CHANGES_REQUESTED: ContentVersion.Status.NEEDS_CHANGES,
            }
            version.status = decision_to_status[decision.decision]
            version.save(update_fields=['status'])

            AuditEvent.objects.create(
                workspace=workspace,
                user=request.user,
                event_type=AuditEvent.EventType.APPROVAL_DECISION_MADE,
                description=(
                    f"'{item.title}' v{version_number}: "
                    f"{decision.get_decision_display()} by {request.user.username}."
                ),
                metadata={
                    "decision_id": str(decision.id),
                    "decision": decision.decision,
                    "content_id": str(item.id),
                    "version_number": version_number,
                }
            )

        return Response(ApprovalDecisionSerializer(decision).data, status=status.HTTP_201_CREATED)


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 6: Review Comments — Collaborative Annotation
# ─────────────────────────────────────────────────────────────────────────────

class ReviewCommentListView(views.APIView):
    """
    GET  /api/content/<content_id>/versions/<version_number>/comments/
         → Lists all collaboration comments on this content version

    POST /api/content/<content_id>/versions/<version_number>/comments/
         → Any workspace member adds a comment (optionally linked to a specific Finding)
    """
    permission_classes = [permissions.IsAuthenticated]

    def _get_version_and_check_access(self, request, content_id, version_number):
        item = get_object_or_404(ContentItem, id=content_id)
        if not WorkspaceMembership.objects.filter(
            workspace=item.workspace,
            user=request.user,
            is_active=True
        ).exists() and not request.user.is_superuser:
            return None, None, Response({"detail": "Access denied."}, status=status.HTTP_403_FORBIDDEN)
        version = get_object_or_404(ContentVersion, content_item=item, version_number=version_number)
        return item, version, None

    def get(self, request, content_id, version_number):
        item, version, error = self._get_version_and_check_access(request, content_id, version_number)
        if error:
            return error

        comments = ReviewComment.objects.filter(content_version=version).select_related('author', 'finding')
        serializer = ReviewCommentSerializer(comments, many=True)
        return Response(serializer.data)

    def post(self, request, content_id, version_number):
        item, version, error = self._get_version_and_check_access(request, content_id, version_number)
        if error:
            return error

        input_serializer = ReviewCommentCreateSerializer(data=request.data)
        if not input_serializer.is_valid():
            return Response(input_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Optional: link this comment to a specific Finding
        finding = None
        if input_serializer.validated_data.get('finding_id'):
            finding = Finding.objects.filter(
                id=input_serializer.validated_data['finding_id'],
                content_version=version
            ).first()

        comment = ReviewComment.objects.create(
            content_version=version,
            finding=finding,
            author=request.user,
            comment_text=input_serializer.validated_data['comment_text'],
        )

        return Response(ReviewCommentSerializer(comment).data, status=status.HTTP_201_CREATED)

