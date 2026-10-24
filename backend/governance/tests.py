from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from workspaces.models import Organisation, ClientWorkspace, WorkspaceMembership
from governance.models import BrandRule, ApprovedClaim, SourceDocument, SourceDocumentVersion
from audit_log.models import AuditEvent

User = get_user_model()

class GovernanceAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.org = Organisation.objects.create(name="Aura Agency Governance Test")

        # Workspaces
        self.ws_ecovolt = ClientWorkspace.objects.create(
            organisation=self.org,
            name="EcoVolt Test",
            slug="ecovolt-gov"
        )
        self.ws_purenest = ClientWorkspace.objects.create(
            organisation=self.org,
            name="PureNest Test",
            slug="purenest-gov"
        )

        # Users
        self.admin_ecovolt = User.objects.create_user(
            username="admin_eco",
            password="AdminPassword123!"
        )
        WorkspaceMembership.objects.create(
            workspace=self.ws_ecovolt,
            user=self.admin_ecovolt,
            role=WorkspaceMembership.Role.ADMIN
        )

        self.creator_ecovolt = User.objects.create_user(
            username="creator_eco",
            password="CreatorPassword123!"
        )
        WorkspaceMembership.objects.create(
            workspace=self.ws_ecovolt,
            user=self.creator_ecovolt,
            role=WorkspaceMembership.Role.CREATOR
        )

        # Pre-seed EcoVolt Brand Rule
        self.eco_rule = BrandRule.objects.create(
            workspace=self.ws_ecovolt,
            name="Prohibit 50% Savings",
            rule_type=BrandRule.RuleType.PROHIBITED_PHRASE,
            pattern_or_phrase="guaranteed 50%",
            preferred_alternative="save up to 20%",
            explanation="Unsupported claim.",
            severity=BrandRule.Severity.CRITICAL
        )

        # Pre-seed PureNest Brand Rule
        self.pure_rule = BrandRule.objects.create(
            workspace=self.ws_purenest,
            name="Prohibit Chemical Free",
            rule_type=BrandRule.RuleType.PROHIBITED_PHRASE,
            pattern_or_phrase="100% chemical-free",
            preferred_alternative="plant-based",
            explanation="Scientifically impossible.",
            severity=BrandRule.Severity.HIGH
        )

    def test_list_rules_strictly_isolated_to_workspace(self):
        """
        CRITICAL TEST: Querying EcoVolt rules returns ONLY EcoVolt rules.
        PureNest rules must NEVER appear in EcoVolt workspace responses.
        """
        token = Token.objects.create(user=self.creator_ecovolt)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        response = self.client.get(f'/api/workspaces/{self.ws_ecovolt.id}/rules/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        rule_names = [r['name'] for r in response.data['results']]
        self.assertIn("Prohibit 50% Savings", rule_names)
        self.assertNotIn("Prohibit Chemical Free", rule_names)

    def test_admin_can_create_brand_rule_and_audits_event(self):
        """Agency Administrator can create a brand rule and an AuditEvent is recorded."""
        token = Token.objects.create(user=self.admin_ecovolt)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        payload = {
            "name": "Mandatory Inverter Disclaimer",
            "rule_type": "REQUIRED_QUALIFIER",
            "pattern_or_phrase": "requires solar inverter",
            "preferred_alternative": "*Requires EcoVolt Home Inverter (sold separately)",
            "explanation": "Must clarify that battery requires compatible inverter.",
            "severity": "HIGH",
            "is_active": True
        }
        response = self.client.post(
            f'/api/workspaces/{self.ws_ecovolt.id}/rules/',
            payload,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], "Mandatory Inverter Disclaimer")

        # Verify AuditEvent was logged
        audit = AuditEvent.objects.filter(
            workspace=self.ws_ecovolt,
            event_type=AuditEvent.EventType.RULE_CREATED
        ).first()
        self.assertIsNotNone(audit)
        self.assertIn("Mandatory Inverter Disclaimer", audit.description)

    def test_content_creator_cannot_create_brand_rules(self):
        """Content Creator role does not have permission to create or alter brand rules."""
        token = Token.objects.create(user=self.creator_ecovolt)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        payload = {
            "name": "Unauthorized Rule Creation",
            "rule_type": "PROHIBITED_PHRASE",
            "pattern_or_phrase": "test",
            "explanation": "test"
        }
        response = self.client.post(
            f'/api/workspaces/{self.ws_ecovolt.id}/rules/',
            payload,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_approved_claim_crud_with_qualifiers(self):
        """Admin can register approved claims with required qualifiers and disallowed variations."""
        token = Token.objects.create(user=self.admin_ecovolt)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        payload = {
            "claim_title": "Peak Shaving Efficiency",
            "permitted_statement": "Reduce peak energy charges by up to 25% with smart scheduling.",
            "required_qualifiers": "Must state 'up to 25%' and include time-of-use footnote.",
            "disallowed_variations": "Guaranteed 25% savings.",
            "category": "Efficiency",
            "is_active": True
        }
        response = self.client.post(
            f'/api/workspaces/{self.ws_ecovolt.id}/claims/',
            payload,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['category'], "Efficiency")

    def test_source_document_and_version_registration(self):
        """Admin can register a source document and append a version with passage excerpts."""
        token = Token.objects.create(user=self.admin_ecovolt)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        # 1. Register Source Document
        doc_payload = {
            "document_code": "SRC-EV-TEST-01",
            "title": "Winter Inverter Performance Benchmarks 2026",
            "description": "Lab stress test in cold weather conditions."
        }
        doc_resp = self.client.post(
            f'/api/workspaces/{self.ws_ecovolt.id}/sources/',
            doc_payload,
            format='json'
        )
        self.assertEqual(doc_resp.status_code, status.HTTP_201_CREATED)
        source_id = doc_resp.data['id']

        # 2. Add Source Version with passage excerpts
        version_payload = {
            "version_label": "v1.0",
            "full_text_content": "Full laboratory report text demonstrating 98.2% inverter efficiency above -10C.",
            "passage_excerpts": [
                {"passage_id": "P01", "text": "demonstrating 98.2% inverter efficiency above -10C"}
            ],
            "effective_date": "2026-01-01",
            "expiration_date": "2027-01-01",
            "is_approved": True
        }
        ver_resp = self.client.post(
            f'/api/sources/{source_id}/versions/',
            version_payload,
            format='json'
        )
        self.assertEqual(ver_resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ver_resp.data['version_label'], "v1.0")
        self.assertTrue(ver_resp.data['is_currently_valid'])

    def test_cross_client_rule_creation_blocked(self):
        """User who is Admin in EcoVolt cannot add rules to PureNest workspace."""
        token = Token.objects.create(user=self.admin_ecovolt)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        payload = {
            "name": "Illegal Cross Workspace Rule",
            "rule_type": "PROHIBITED_PHRASE",
            "pattern_or_phrase": "cross client phrase",
            "explanation": "Should be blocked"
        }
        # Attempting to post to PureNest workspace
        response = self.client.post(
            f'/api/workspaces/{self.ws_purenest.id}/rules/',
            payload,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
