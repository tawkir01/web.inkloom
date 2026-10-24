from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    LoginView, 
    LogoutView, 
    CurrentUserView, 
    WorkspaceViewSet, 
    WorkspaceMembersView
)

router = DefaultRouter()
router.register(r'workspaces', WorkspaceViewSet, basename='workspaces')

urlpatterns = [
    # Authentication endpoints
    path('auth/login/', LoginView.as_view(), name='auth-login'),
    path('auth/logout/', LogoutView.as_view(), name='auth-logout'),
    path('auth/me/', CurrentUserView.as_view(), name='auth-me'),

    # Workspace member management
    path('workspaces/<uuid:workspace_id>/members/', WorkspaceMembersView.as_view(), name='workspace-members'),

    # Router endpoints (GET /api/workspaces/, GET /api/workspaces/<id>/)
    path('', include(router.urls)),
]
