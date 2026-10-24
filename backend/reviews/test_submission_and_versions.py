from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from workspaces.models import Organisation, ClientWorkspace, WorkspaceMembership
from reviews.models import ContentItem, ContentVersion, ApprovalDecision
from audit_log.models import AuditEvent

User = get_user_model()

class ContentSubmissionAndVersionAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.org = Organisation.objects.create(name="Aura Content Submissions Test")

        # Workspaces
        self.ws_a = ClientWorkspace.objects.create(organisation=self.org, name="EcoVolt Sub Test", slug="ev-sub")
        self.ws_b = ClientWorkspace.objects.create(organisation=self.org, name="PureNest Sub Test", slug="pn-sub")

        # Users
        self.creator_a = User.objects.create_user(username="creator_a", password="Password123!")
        WorkspaceMembership.objects.create(
            workspace=self.ws_a, user=self.creator_a, role=WorkspaceMembership.Role.CREATOR
        )

        self.reviewer_a = User.objects.create_user(username="reviewer_a", password="Password123!")
        WorkspaceMembership.objects.create(
            workspace=self.ws_a, user=self.reviewer_a, role=WorkspaceMembership.Role.REVIEWER
        )

        self.user_b = User.objects.create_user(username="user_b", password="Password123!")
        WorkspaceMembership.objects.create(
            workspace=self.ws_b, user=self.user_b, role=WorkspaceMembership.Role.CREATOR
        )

    def test_submit_content_creates_item_and_version_1(self):
        """Content Creator can submit copy; creates ContentItem and ContentVersion v1 with SHA-256."""
        token = Token.objects.create(user=self.creator_a)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        payload = {
            "title": "Spring Smart Thermostat Launch",
            "description": "Email newsletter announcement",
            "raw_text": "EcoVolt Smart Thermostat helps you save up to 20% on heating and cooling bills."
        }
        response = self.client.post(
            f'/api/workspaces/{self.ws_a.id}/content/',
            payload,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], "Spring Smart Thermostat Launch")
        self.assertEqual(len(response.data['versions']), 1)

        v1 = response.data['versions'][0]
        self.assertEqual(v1['version_number'], 1)
        self.assertEqual(v1['status'], "SUBMITTED")
        self.assertTrue(len(v1['checksum_sha256']) == 64)

        # AuditEvent verified
        audit = AuditEvent.objects.filter(
            workspace=self.ws_a,
            event_type=AuditEvent.EventType.CONTENT_SUBMITTED
        ).first()
        self.assertIsNotNone(audit)
        self.assertIn("Spring Smart Thermostat Launch", audit.description)

    def test_empty_content_submission_rejected(self):
        """Submitting empty copy text must return 400 Bad Request."""
        token = Token.objects.create(user=self.creator_a)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        payload = {
            "title": "Empty Post",
            "raw_text": "   "
        }
        response = self.client.post(
            f'/api/workspaces/{self.ws_a.id}/content/',
            payload,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_workspace_content_list_includes_versions_for_review_workspace(self):
        token = Token.objects.create(user=self.creator_a)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        item = ContentItem.objects.create(
            workspace=self.ws_a,
            title="Review workspace content",
            created_by=self.creator_a,
        )
        ContentVersion.objects.create(
            content_item=item,
            version_number=1,
            raw_text="First version",
            created_by=self.creator_a,
        )
        ContentVersion.objects.create(
            content_item=item,
            version_number=2,
            raw_text="Latest version",
            created_by=self.creator_a,
        )

        response = self.client.get(f'/api/workspaces/{self.ws_a.id}/content/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        listed_item = next(entry for entry in response.data if entry['id'] == str(item.id))
        self.assertEqual(
            [version['version_number'] for version in listed_item['versions']],
            [2, 1],
        )
        self.assertEqual(listed_item['versions'][0]['raw_text'], "Latest version")

    def test_spawn_revision_creates_version_2_without_inheriting_approval(self):
        """
        CRITICAL COMPLIANCE TEST:
        1. Creator submits v1.
        2. Reviewer approves v1.
        3. Creator submits revision (v2).
        4. v2 must NOT inherit approval! It must be in SUBMITTED state.
        """
        token_creator = Token.objects.create(user=self.creator_a)
        token_reviewer = Token.objects.create(user=self.reviewer_a)

        # 1. Create ContentItem + v1
        item = ContentItem.objects.create(
            workspace=self.ws_a,
            title="Clean Power Ad",
            created_by=self.creator_a
        )
        v1 = ContentVersion.objects.create(
            content_item=item,
            version_number=1,
            raw_text="EcoVolt saves up to 20% on energy costs.",
            status=ContentVersion.Status.APPROVED,
            created_by=self.creator_a
        )
        # Approval decision on v1
        ApprovalDecision.objects.create(
            content_version=v1,
            reviewer=self.reviewer_a,
            decision=ApprovalDecision.Decision.APPROVED,
            decision_notes="Approved."
        )

        # 2. Creator submits revision -> v2
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token_creator.key}')
        revision_payload = {
            "raw_text": "EcoVolt saves up to 20% on energy costs! Sign up for free installation."
        }
        rev_resp = self.client.post(
            f'/api/content/{item.id}/versions/',
            revision_payload,
            format='json'
        )

        self.assertEqual(rev_resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(rev_resp.data['version_number'], 2)
        self.assertEqual(rev_resp.data['status'], "SUBMITTED")
        # Ensure has_approval is FALSE on v2
        self.assertFalse(rev_resp.data['has_approval'])

        # Check total versions is 2
        self.assertEqual(item.versions.count(), 2)

    def test_cross_client_content_access_blocked(self):
        """User in Workspace B cannot retrieve content from Workspace A."""
        token_b = Token.objects.create(user=self.user_b)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token_b.key}')

        item_a = ContentItem.objects.create(
            workspace=self.ws_a,
            title="Confidential Workspace A Campaign",
            created_by=self.creator_a
        )

        response = self.client.get(f'/api/content/{item_a.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
