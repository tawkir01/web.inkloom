from rest_framework import status, views, viewsets, permissions
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.shortcuts import get_object_or_404
from .models import ClientWorkspace, WorkspaceMembership
from .serializers import (
    UserProfileSerializer, 
    ClientWorkspaceSerializer, 
    WorkspaceMembershipSummarySerializer,
    WorkspaceMemberDetailSerializer
)
from .permissions import IsWorkspaceMember, IsWorkspaceAdmin
from audit_log.models import AuditEvent

User = get_user_model()

class LoginView(views.APIView):
    """
    Authenticates a user by username.
    Returns auth token, user profile, and accessible workspaces.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username', '')
        password = request.data.get('password', '')

        if not isinstance(username, str) or not isinstance(password, str):
            return Response(
                {"detail": "Username and password must be text values."},
                status=status.HTTP_400_BAD_REQUEST
            )

        username = username.strip()
        if not username or not password:
            return Response(
                {"detail": "Please provide both a username and password."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(request, username=username, password=password)
        if not user:
            return Response(
                {"detail": "Invalid username or password."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        login(request, user)
        token, _ = Token.objects.get_or_create(user=user)

        memberships = WorkspaceMembership.objects.filter(
            user=user, 
            is_active=True
        ).select_related('workspace')

        return Response({
            "token": token.key,
            "user": UserProfileSerializer(user).data,
            "memberships": WorkspaceMembershipSummarySerializer(memberships, many=True).data
        })


class LogoutView(views.APIView):
    """
    Invalidates current authentication token and closes session.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        logout(request)
        return Response({"detail": "Successfully logged out."}, status=status.HTTP_200_OK)


class CurrentUserView(views.APIView):
    """
    Returns current authenticated user profile and all assigned client workspace memberships.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        memberships = WorkspaceMembership.objects.filter(
            user=request.user, 
            is_active=True
        ).select_related('workspace')

        return Response({
            "user": UserProfileSerializer(request.user).data,
            "memberships": WorkspaceMembershipSummarySerializer(memberships, many=True).data
        })


class WorkspaceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Lists and retrieves client workspaces accessible to the authenticated user.
    Strict tenant isolation: Only returns workspaces where the user has an active membership.
    """
    serializer_class = ClientWorkspaceSerializer
    permission_classes = [permissions.IsAuthenticated, IsWorkspaceMember]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return ClientWorkspace.objects.none()

        # Regular users only see workspaces where they have active membership
        return ClientWorkspace.objects.filter(
            memberships__user=user,
            memberships__is_active=True,
            is_active=True
        ).distinct()


class WorkspaceMembersView(views.APIView):
    """
    Manages workspace memberships and user roles.
    Listing: requires membership in the workspace.
    Modifying/Adding: requires Agency Administrator role in this workspace.
    """
    permission_classes = [permissions.IsAuthenticated, IsWorkspaceMember]

    def get_workspace(self, workspace_id):
        return get_object_or_404(ClientWorkspace, id=workspace_id, is_active=True)

    def get(self, request, workspace_id):
        workspace = self.get_workspace(workspace_id)
        # Ensure user is a member
        self.check_object_permissions(request, workspace)

        members = WorkspaceMembership.objects.filter(
            workspace=workspace
        ).select_related('user')
        serializer = WorkspaceMemberDetailSerializer(members, many=True)
        return Response(serializer.data)

    def post(self, request, workspace_id):
        workspace = self.get_workspace(workspace_id)
        # Requires Admin role in this workspace
        if not WorkspaceMembership.objects.filter(
            workspace=workspace, 
            user=request.user, 
            role=WorkspaceMembership.Role.ADMIN,
            is_active=True
        ).exists() and not request.user.is_superuser:
            return Response(
                {"detail": "Only Agency Administrators for this workspace can manage memberships."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = WorkspaceMemberDetailSerializer(data=request.data)
        if serializer.is_valid():
            membership, created = WorkspaceMembership.objects.update_or_create(
                workspace=workspace,
                user=serializer.validated_data['user'],
                role=serializer.validated_data.get('role', WorkspaceMembership.Role.CREATOR),
                defaults={'is_active': serializer.validated_data.get('is_active', True)}
            )

            # Audit logging
            AuditEvent.objects.create(
                workspace=workspace,
                user=request.user,
                event_type=AuditEvent.EventType.MEMBERSHIP_CHANGED,
                description=f"User {membership.user.username} role set to {membership.get_role_display()} in {workspace.name}.",
                metadata={"target_user_id": str(membership.user.id), "role": membership.role}
            )

            return Response(
                WorkspaceMemberDetailSerializer(membership).data, 
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
