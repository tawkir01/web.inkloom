from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from .models import Organisation, ClientWorkspace, WorkspaceMembership

User = get_user_model()

class WorkspaceModelTests(TestCase):
    def setUp(self):
        self.org = Organisation.objects.create(name="Aura Global Media")
        self.user = User.objects.create_user(username="creator_jane", password="securepassword123")
        self.workspace = ClientWorkspace.objects.create(
            organisation=self.org,
            name="EcoVolt Energy",
            industry="Energy Solutions"
        )

    def test_organisation_slug_auto_generated(self):
        """Organisation slug should be generated automatically from the name."""
        self.assertEqual(self.org.slug, "aura-global-media")

    def test_workspace_slug_auto_generated(self):
        """ClientWorkspace slug should be generated automatically from the name."""
        self.assertEqual(self.workspace.slug, "ecovolt-energy")

    def test_workspace_membership_creation(self):
        """Users can be assigned roles in specific client workspaces."""
        membership = WorkspaceMembership.objects.create(
            workspace=self.workspace,
            user=self.user,
            role=WorkspaceMembership.Role.CREATOR
        )
        self.assertEqual(membership.role, "CONTENT_CREATOR")
        self.assertTrue(membership.is_active)

    def test_duplicate_membership_prevented_by_unique_constraint(self):
        """A user cannot have duplicate active roles in the same workspace."""
        WorkspaceMembership.objects.create(
            workspace=self.workspace,
            user=self.user,
            role=WorkspaceMembership.Role.CREATOR
        )
        with self.assertRaises(IntegrityError):
            WorkspaceMembership.objects.create(
                workspace=self.workspace,
                user=self.user,
                role=WorkspaceMembership.Role.CREATOR
            )
