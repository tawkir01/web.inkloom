import json
from unittest.mock import Mock, patch

import requests
from django.test import TestCase, override_settings

from governance.models import SourceDocument, SourceDocumentVersion
from reviews.ai_adapter import analyze_claims
from workspaces.models import ClientWorkspace, Organisation

class AIAdapterTests(TestCase):
    def setUp(self):
        organisation = Organisation.objects.create(name="AI Adapter Test")
        self.workspace = ClientWorkspace.objects.create(
            organisation=organisation,
            name="AI Test Workspace",
            slug="ai-test-workspace",
        )
        self.source = SourceDocument.objects.create(
            workspace=self.workspace,
            title="Test evidence",
            document_code="SRC-AI-01",
        )
        self.source_version = SourceDocumentVersion.objects.create(
            source_document=self.source,
            version_label="v1",
            full_text_content="Café battery saves 20% during tests.",
            passage_excerpts=[
                {
                    "passage_id": "P1",
                    "text": "Café battery saves 20% during tests.",
                },
            ],
        )

    @override_settings(
        AI_PROVIDER="openai",
        AI_API_KEY="test-only-key",
        AI_MODEL_NAME="test-model",
    )
    @patch("reviews.ai_adapter.requests.post")
    def test_valid_model_findings_use_only_real_source_and_exact_offsets(
        self,
        mock_post,
    ):
        response = Mock()
        response.json.return_value = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "findings": [{
                            "claim_text": "Café battery saves 20% during tests.",
                            "verification_status": "SUPPORTED",
                            "explanation": "The wording matches the approved evidence.",
                            "evidence_refs": [f"{self.source_version.id}:P1"],
                            "confidence": 0.9,
                        }],
                    }),
                },
            }],
        }
        mock_post.return_value = response
        text = "🚀 Café battery saves 20% during tests."

        result = analyze_claims(text, self.workspace)

        self.assertEqual(result.status, "COMPLETED")
        self.assertEqual(len(result.findings), 1)
        finding = result.findings[0]
        self.assertEqual(text[finding.start_char:finding.end_char], finding.flagged_text)
        self.assertEqual(finding.flagged_text, "Café battery saves 20% during tests.")
        self.assertEqual(finding.source_version_id, self.source_version.id)
        self.assertEqual(finding.source_passage_id, "P1")
        self.assertEqual(
            finding.quoted_passage,
            "Café battery saves 20% during tests.",
        )
        self.assertTrue(finding.is_citation_validated)
        self.assertEqual(
            mock_post.call_args.kwargs["headers"]["Authorization"],
            "Bearer test-only-key",
        )

    @override_settings(
        AI_PROVIDER="openai",
        AI_API_KEY="test-only-key",
        AI_MODEL_NAME="test-model",
    )
    @patch("reviews.ai_adapter.requests.post")
    def test_invalid_evidence_reference_fails_closed(self, mock_post):
        response = Mock()
        response.json.return_value = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "findings": [{
                            "claim_text": "Café battery saves 20% during tests.",
                            "verification_status": "SUPPORTED",
                            "explanation": "Unsupported reference.",
                            "evidence_refs": ["another-workspace:PRIVATE"],
                        }],
                    }),
                },
            }],
        }
        mock_post.return_value = response

        result = analyze_claims(
            "Café battery saves 20% during tests.",
            self.workspace,
        )

        self.assertEqual(result.status, "FAILED")
        self.assertEqual(result.findings, [])
        self.assertNotIn("another-workspace", result.error_message)

    @override_settings(
        AI_PROVIDER="openai",
        AI_API_KEY="",
        AI_MODEL_NAME="test-model",
    )
    @patch("reviews.ai_adapter.requests.post")
    def test_missing_api_key_keeps_deterministic_review_available(self, mock_post):
        result = analyze_claims(
            "A factual claim with no configured AI provider.",
            self.workspace,
        )

        self.assertEqual(result.status, "NOT_CONFIGURED")
        self.assertEqual(result.findings, [])
        mock_post.assert_not_called()

    @override_settings(
        AI_PROVIDER="openai",
        AI_API_KEY="test-only-key",
        AI_MODEL_NAME="test-model",
    )
    @patch(
        "reviews.ai_adapter.requests.post",
        side_effect=requests.Timeout,
    )
    def test_provider_timeout_is_reported_as_ai_failure(self, _mock_post):
        result = analyze_claims(
            "A factual claim with a slow provider.",
            self.workspace,
        )

        self.assertEqual(result.status, "FAILED")
        self.assertEqual(result.findings, [])
        self.assertIn("timed out", result.error_message)
