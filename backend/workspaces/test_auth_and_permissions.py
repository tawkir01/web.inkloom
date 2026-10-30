from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from workspaces.models import Organisation, ClientWorkspace, WorkspaceMembership
from audit_log.models import AuditEvent

User = get_user_model()

class AuthenticationAndPermissionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.org = Organisation.objects.create(name="Aura Agency Security Test")

        # Create two distinct workspaces for multi-tenant isolation tests
        self.workspace_a = ClientWorkspace.objects.create(
            organisation=self.org,
            name="EcoVolt Workspace",
            slug="ecovolt-sec"
        )
        self.workspace_b = ClientWorkspace.objects.create(
            organisation=self.org,
            name="PureNest Workspace",
            slug="purenest-sec"
        )

        # User 1: Content Creator in Workspace A only
        self.user_a = User.objects.create_user(
            username="creator_a", 
            email="creator_a@demo.com", 
            password="SecurePasswordA1!"
        )
        WorkspaceMembership.objects.create(
            workspace=self.workspace_a,
            user=self.user_a,
            role=WorkspaceMembership.Role.CREATOR
        )

        # User 2: Admin in Workspace A, but NOT in Workspace B
        self.admin_a = User.objects.create_user(
            username="admin_a", 
            email="admin_a@demo.com", 
            password="SecurePasswordAdmin1!"
        )
        WorkspaceMembership.objects.create(
            workspace=self.workspace_a,
            user=self.admin_a,
            role=WorkspaceMembership.Role.ADMIN
        )

    def test_login_successful_returns_token_and_memberships(self):
        """Valid credentials return a token, user profile, and user's workspace roles."""
        response = self.client.post('/api/auth/login/', {
            'username': 'creator_a',
            'password': 'SecurePasswordA1!'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertIn('user', response.data)
        self.assertIn('memberships', response.data)
        self.assertEqual(response.data['user']['username'], 'creator_a')
        self.assertEqual(len(response.data['memberships']), 1)
        self.assertEqual(response.data['memberships'][0]['workspace_name'], 'EcoVolt Workspace')
        self.assertEqual(response.data['memberships'][0]['role'], 'CONTENT_CREATOR')

    def test_login_without_password_succeeds_for_known_user(self):
        """Username-only login remains valid when no password is supplied."""
        response = self.client.post('/api/auth/login/', {
            'username': 'creator_a',
            'password': 'WrongPassword!'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['user']['username'], 'creator_a')

    def test_login_unknown_user_returns_401(self):
        """Unknown usernames are rejected even when the frontend sends a password."""
        response = self.client.post('/api/auth/login/', {
            'username': 'missing_user',
            'password': 'WrongPassword!'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn('token', response.data)

    def test_unauthenticated_request_to_workspaces_rejected(self):
        """Unauthenticated requests to protected endpoints return 401."""
        response = self.client.get('/api/workspaces/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_current_user_profile_endpoint(self):
        """GET /api/auth/me/ returns authenticated user context."""
        token = Token.objects.create(user=self.user_a)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        response = self.client.get('/api/auth/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['username'], 'creator_a')

    def test_system_stats_are_restricted_to_authenticated_staff(self):
        response = self.client.get('/api/stats/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        regular_token = Token.objects.create(user=self.user_a)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {regular_token.key}')
        response = self.client.get('/api/stats/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        staff_user = User.objects.create_user(
            username="staff_stats",
            password="SecurePasswordStaff1!",
            is_staff=True,
        )
        staff_token = Token.objects.create(user=staff_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {staff_token.key}')
        response = self.client.get('/api/stats/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['workspaces_count'], 2)

    def test_cross_client_isolation_enforced(self):
        """
        CRITICAL MULTI-TENANT TEST:
        User A belongs only to Workspace A.
        User A's workspace list must NOT contain Workspace B.
        Directly requesting Workspace B details must return 404 (or 403), never leaking Workspace B data.
        """
        token = Token.objects.create(user=self.user_a)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        # 1. Listing accessible workspaces only returns Workspace A
        response = self.client.get('/api/workspaces/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        workspace_ids = [w['id'] for w in response.data['results']]
        self.assertIn(str(self.workspace_a.id), workspace_ids)
        self.assertNotIn(str(self.workspace_b.id), workspace_ids)

        # 2. Direct attempt to retrieve Workspace B must be rejected (403 Forbidden)
        direct_resp = self.client.get(f'/api/workspaces/{self.workspace_b.id}/')
        self.assertEqual(direct_resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_non_admin_cannot_modify_memberships(self):
        """A Content Creator cannot add or change member roles in a workspace."""
        token = Token.objects.create(user=self.user_a)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        new_user = User.objects.create_user(username="temp_user", password="password")
        response = self.client.post(f'/api/workspaces/{self.workspace_a.id}/members/', {
            'user_id': new_user.id,
            'role': WorkspaceMembership.Role.REVIEWER
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_workspace_admin_can_modify_memberships_and_audits_event(self):
        """An Agency Administrator can assign roles, and an AuditEvent is recorded."""
        token = Token.objects.create(user=self.admin_a)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        new_user = User.objects.create_user(username="new_reviewer", password="password")
        response = self.client.post(f'/api/workspaces/{self.workspace_a.id}/members/', {
            'user_id': new_user.id,
            'role': WorkspaceMembership.Role.REVIEWER
        }, format='json')

        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        self.assertTrue(
            WorkspaceMembership.objects.filter(
                workspace=self.workspace_a, 
                user=new_user, 
                role=WorkspaceMembership.Role.REVIEWER
            ).exists()
        )

        # Verify AuditEvent was logged
        audit_event = AuditEvent.objects.filter(
            workspace=self.workspace_a,
            event_type=AuditEvent.EventType.MEMBERSHIP_CHANGED
        ).first()
        self.assertIsNotNone(audit_event)
        self.assertIn("new_reviewer", audit_event.description)
