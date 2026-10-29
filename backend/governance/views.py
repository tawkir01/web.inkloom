from rest_framework import viewsets, permissions, status, views
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models.deletion import ProtectedError
from workspaces.models import ClientWorkspace, WorkspaceMembership
from workspaces.permissions import IsWorkspaceMember, IsWorkspaceAdmin
from .models import BrandRule, ApprovedClaim, SourceDocument, SourceDocumentVersion, BrandAsset
from .serializers import (
    BrandRuleSerializer,
    ApprovedClaimSerializer,
    SourceDocumentSerializer,
    SourceDocumentVersionSerializer,
    BrandAssetSerializer
)
from audit_log.models import AuditEvent

class WorkspaceScopedMixin:
    """
    Mixin that extracts and validates the workspace from URL kwargs.
    Enforces that queries are strictly isolated to the specified workspace.
    """
    def get_workspace(self):
        workspace_id = self.kwargs.get('workspace_id')
        return get_object_or_404(ClientWorkspace, id=workspace_id, is_active=True)

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated, IsWorkspaceMember]
        else:
            # Mutations require Agency Administrator privileges
            permission_classes = [permissions.IsAuthenticated, IsWorkspaceAdmin]
        return [permission() for permission in permission_classes]


class BrandRuleViewSet(WorkspaceScopedMixin, viewsets.ModelViewSet):
    """
    CRUD API for brand rules strictly scoped to the workspace.
    """
    serializer_class = BrandRuleSerializer

    def get_queryset(self):
        workspace = self.get_workspace()
        queryset = BrandRule.objects.filter(workspace=workspace)
        rule_type = self.request.query_params.get('rule_type')
        severity = self.request.query_params.get('severity')
        is_active = self.request.query_params.get('is_active')

        if rule_type:
            queryset = queryset.filter(rule_type=rule_type)
        if severity:
            queryset = queryset.filter(severity=severity)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        return queryset

    def perform_create(self, serializer):
        workspace = self.get_workspace()
        rule = serializer.save(workspace=workspace)
        AuditEvent.objects.create(
            workspace=workspace,
            user=self.request.user,
            event_type=AuditEvent.EventType.RULE_CREATED,
            description=f"Brand rule '{rule.name}' ({rule.get_rule_type_display()}) created.",
            metadata={"rule_id": str(rule.id), "severity": rule.severity}
        )

    def perform_update(self, serializer):
        rule = serializer.save()
        AuditEvent.objects.create(
            workspace=rule.workspace,
            user=self.request.user,
            event_type=AuditEvent.EventType.RULE_MODIFIED,
            description=f"Brand rule '{rule.name}' modified.",
            metadata={"rule_id": str(rule.id)}
        )


class ApprovedClaimViewSet(WorkspaceScopedMixin, viewsets.ModelViewSet):
    """
    CRUD API for vetted marketing claims strictly scoped to the workspace.
    """
    serializer_class = ApprovedClaimSerializer

    def get_queryset(self):
        workspace = self.get_workspace()
        queryset = ApprovedClaim.objects.filter(workspace=workspace)
        category = self.request.query_params.get('category')
        is_active = self.request.query_params.get('is_active')

        if category:
            queryset = queryset.filter(category__iexact=category)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        return queryset

    def perform_create(self, serializer):
        workspace = self.get_workspace()
        serializer.save(workspace=workspace)


class SourceDocumentViewSet(WorkspaceScopedMixin, viewsets.ModelViewSet):
    """
    CRUD API for catalog of evidentiary source documents.
    """
    serializer_class = SourceDocumentSerializer

    def get_queryset(self):
        workspace = self.get_workspace()
        return (
            SourceDocument.objects.filter(workspace=workspace)
            .prefetch_related('versions')
            .order_by('document_code')
        )

    def perform_create(self, serializer):
        workspace = self.get_workspace()
        source = serializer.save(workspace=workspace)
        AuditEvent.objects.create(
            workspace=workspace,
            user=self.request.user,
            event_type=AuditEvent.EventType.SOURCE_ADDED,
            description=f"Source document '{source.document_code}: {source.title}' registered.",
            metadata={"source_id": str(source.id), "code": source.document_code}
        )

    def destroy(self, request, *args, **kwargs):
        source = self.get_object()
        if source.versions.exists():
            return Response(
                {"detail": "Source documents with version history cannot be deleted."},
                status=status.HTTP_409_CONFLICT
            )
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {"detail": "This source document is referenced and cannot be deleted."},
                status=status.HTTP_409_CONFLICT
            )


class SourceDocumentVersionCreateView(views.APIView):
    """
    Registers a new immutable version of an existing source document with passages and effective dates.
    Requires Agency Administrator role in the source document's workspace.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, source_id):
        source_doc = get_object_or_404(SourceDocument, id=source_id)

        # Enforce Admin in this workspace
        if not WorkspaceMembership.objects.filter(
            workspace=source_doc.workspace,
            user=request.user,
            role=WorkspaceMembership.Role.ADMIN,
            is_active=True
        ).exists() and not request.user.is_superuser:
            return Response(
                {"detail": "Only Agency Administrators for this workspace can add source document versions."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = SourceDocumentVersionSerializer(data=request.data)
        if serializer.is_valid():
            version = serializer.save(source_document=source_doc)
            AuditEvent.objects.create(
                workspace=source_doc.workspace,
                user=request.user,
                event_type=AuditEvent.EventType.SOURCE_MODIFIED,
                description=f"New version '{version.version_label}' added for source {source_doc.document_code}.",
                metadata={"source_id": str(source_doc.id), "version_id": str(version.id)}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BrandAssetViewSet(WorkspaceScopedMixin, viewsets.ModelViewSet):
    """
    Manages brand logos and marketing packaging images.
    """
    serializer_class = BrandAssetSerializer

    def get_queryset(self):
        workspace = self.get_workspace()
        return BrandAsset.objects.filter(workspace=workspace)

    def perform_create(self, serializer):
        workspace = self.get_workspace()
        serializer.save(workspace=workspace)
