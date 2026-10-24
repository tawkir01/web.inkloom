from rest_framework import permissions
from .models import WorkspaceMembership, ClientWorkspace

class IsWorkspaceMember(permissions.BasePermission):
    """
    Permission check ensuring the requesting user belongs to the target workspace.
    Accepts workspace UUID passed either via URL kwarg ('workspace_id' or 'pk') or object attribute.
    """
    message = "You are not an active member of this client workspace."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        workspace_id = view.kwargs.get('workspace_id') or view.kwargs.get('pk')
        if not workspace_id:
            return True  # Object-level permission will handle it

        return WorkspaceMembership.objects.filter(
            workspace_id=workspace_id,
            user=request.user,
            is_active=True
        ).exists()

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        workspace = obj if isinstance(obj, ClientWorkspace) else getattr(obj, 'workspace', None)
        if not workspace and hasattr(obj, 'content_item'):
            workspace = obj.content_item.workspace

        if not workspace:
            return False

        return WorkspaceMembership.objects.filter(
            workspace=workspace,
            user=request.user,
            is_active=True
        ).exists()


class HasWorkspaceRole(permissions.BasePermission):
    """
    Parametrized permission ensuring the user possesses specific roles within the target workspace.
    """
    allowed_roles = []
    message = "Your role in this workspace does not permit this action."

    def __init__(self, allowed_roles=None):
        if allowed_roles:
            self.allowed_roles = allowed_roles

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        workspace_id = view.kwargs.get('workspace_id') or view.kwargs.get('pk')
        if not workspace_id:
            return True

        return WorkspaceMembership.objects.filter(
            workspace_id=workspace_id,
            user=request.user,
            role__in=self.allowed_roles,
            is_active=True
        ).exists()

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        workspace = obj if isinstance(obj, ClientWorkspace) else getattr(obj, 'workspace', None)
        if not workspace and hasattr(obj, 'content_item'):
            workspace = obj.content_item.workspace

        if not workspace:
            return False

        return WorkspaceMembership.objects.filter(
            workspace=workspace,
            user=request.user,
            role__in=self.allowed_roles,
            is_active=True
        ).exists()


class IsWorkspaceAdmin(HasWorkspaceRole):
    allowed_roles = [WorkspaceMembership.Role.ADMIN]
    message = "Agency Administrator role required for this workspace operation."


class IsBrandReviewer(HasWorkspaceRole):
    allowed_roles = [WorkspaceMembership.Role.REVIEWER]
    message = "Only an authorized Brand Reviewer for this workspace can approve or reject content."


class IsContentCreator(HasWorkspaceRole):
    allowed_roles = [WorkspaceMembership.Role.CREATOR, WorkspaceMembership.Role.ADMIN]
    message = "Content Creator permission required to submit copy or media."


class IsAccountManager(HasWorkspaceRole):
    allowed_roles = [WorkspaceMembership.Role.MANAGER, WorkspaceMembership.Role.ADMIN]
    message = "Account Manager or Administrator access required."
