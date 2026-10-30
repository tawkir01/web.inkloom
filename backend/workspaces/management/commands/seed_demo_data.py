from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from workspaces.models import Organisation, ClientWorkspace, WorkspaceMembership
from governance.models import BrandRule, ApprovedClaim, SourceDocument, SourceDocumentVersion
from reviews.models import ContentItem, ContentVersion, ReviewRun, Finding, ApprovalDecision
from audit_log.models import AuditEvent

User = get_user_model()

class Command(BaseCommand):
    help = "Seeds clearly labelled fictional demo data for EcoVolt, PureNest, and FinEdge"

    def get_demo_user(self, username, email, first_name, last_name):
        user, _ = User.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
            },
        )
        user.set_unusable_password()
        user.is_staff = False
        user.is_superuser = False
        user.save(update_fields=["password", "is_staff", "is_superuser"])
        return user

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding fictional demo data for Inkloom Guardian..."))

        # 1. Create Organization
        org, _ = Organisation.objects.get_or_create(
            name="Aura Global Agency [FICTIONAL]",
            defaults={"description": "Demonstration agency holding multiple client workspaces"}
        )

        # 2. Create non-login users to attribute illustrative records and events
        admin_user = self.get_demo_user("agency_admin", "admin@aurademo.com", "Alex", "Admin")
        creator_user = self.get_demo_user("content_creator", "creator@aurademo.com", "Casey", "Creator")
        manager_user = self.get_demo_user("account_manager", "manager@aurademo.com", "Morgan", "Manager")
        reviewer_user = self.get_demo_user("brand_reviewer", "reviewer@aurademo.com", "Riley", "Reviewer")

        # 3. Workspaces
        # Client A: EcoVolt (Energy Solutions)
        ecovolt, _ = ClientWorkspace.objects.get_or_create(
            organisation=org,
            slug="ecovolt",
            defaults={
                "name": "EcoVolt [FICTIONAL DEMO]",
                "industry": "Renewable Energy & Home Efficiency",
                "description": "Smart energy storage and solar heating systems."
            }
        )

        # Client B: PureNest (Home Care Products)
        purenest, _ = ClientWorkspace.objects.get_or_create(
            organisation=org,
            slug="purenest",
            defaults={
                "name": "PureNest [FICTIONAL DEMO]",
                "industry": "Organic Home Care & Cleaning",
                "description": "Plant-based household cleaning and laundry supplies."
            }
        )

        # Client C: FinEdge (Financial Education)
        finedge, _ = ClientWorkspace.objects.get_or_create(
            organisation=org,
            slug="finedge",
            defaults={
                "name": "FinEdge [FICTIONAL DEMO]",
                "industry": "Financial Literacy & Education",
                "description": "Consumer personal finance and investment coaching."
            }
        )

        # 4. Assign Workspace Memberships
        for ws in [ecovolt, purenest, finedge]:
            WorkspaceMembership.objects.get_or_create(
                workspace=ws, user=admin_user, role=WorkspaceMembership.Role.ADMIN
            )
            WorkspaceMembership.objects.get_or_create(
                workspace=ws, user=creator_user, role=WorkspaceMembership.Role.CREATOR
            )
            WorkspaceMembership.objects.get_or_create(
                workspace=ws, user=manager_user, role=WorkspaceMembership.Role.MANAGER
            )
            WorkspaceMembership.objects.get_or_create(
                workspace=ws, user=reviewer_user, role=WorkspaceMembership.Role.REVIEWER
            )

        # 5. Populate EcoVolt Rules & Sources
        # Source Doc
        src_ev, _ = SourceDocument.objects.get_or_create(
            workspace=ecovolt,
            document_code="SRC-EV-2025-01",
            defaults={"title": "EcoVolt Home Energy Benchmark Study 2025"}
        )
        src_ev_v1, _ = SourceDocumentVersion.objects.get_or_create(
            source_document=src_ev,
            version_label="v1.0",
            defaults={
                "full_text_content": (
                    "Laboratory trial benchmark EV-2025-Q3: Controlled testing across 450 residential homes "
                    "demonstrated that homeowners save up to 20% on annual energy consumption when pairing "
                    "the EcoVolt Smart Thermostat with our solar storage inverter. Savings depend on insulation "
                    "quality and climate zones. No guarantee of 100% or 50% savings is substantiated."
                ),
                "passage_excerpts": [
                    {
                        "passage_id": "EV-P01",
                        "text": "homeowners save up to 20% on annual energy consumption when pairing the EcoVolt Smart Thermostat"
                    },
                    {
                        "passage_id": "EV-P02",
                        "text": "No guarantee of 100% or 50% savings is substantiated."
                    }
                ]
            }
        )

        # Approved Claim
        ApprovedClaim.objects.get_or_create(
            workspace=ecovolt,
            claim_title="Annual Energy Savings",
            defaults={
                "permitted_statement": "Save up to 20% on annual energy bills with EcoVolt smart storage.",
                "required_qualifiers": "Must always include 'up to 20%'. Never state guaranteed or fixed percentages.",
                "disallowed_variations": "Guaranteed 50% savings, 100% free electric power.",
                "category": "Efficiency"
            }
        )

        # Brand Rules
        BrandRule.objects.get_or_create(
            workspace=ecovolt,
            name="Prohibit Guaranteed Savings Claims",
            defaults={
                "rule_type": BrandRule.RuleType.PROHIBITED_PHRASE,
                "pattern_or_phrase": "guaranteed 50%",
                "preferred_alternative": "save up to 20%",
                "explanation": "Guaranteed absolute savings claims contradict lab benchmarks and violate FTC regulations.",
                "severity": BrandRule.Severity.CRITICAL
            }
        )

        BrandRule.objects.get_or_create(
            workspace=ecovolt,
            name="Mandatory Trademark Spelling",
            defaults={
                "rule_type": BrandRule.RuleType.REQUIRED_TERM,
                "pattern_or_phrase": "ecovolt",
                "preferred_alternative": "EcoVolt™",
                "explanation": "Brand names must always use CamelCase with trademark symbol.",
                "severity": BrandRule.Severity.LOW
            }
        )

        # 6. Populate PureNest Rules & Sources
        src_pn, _ = SourceDocument.objects.get_or_create(
            workspace=purenest,
            document_code="SRC-PN-2026-BIO",
            defaults={"title": "PureNest Dermatological & Biodegradability Study"}
        )
        SourceDocumentVersion.objects.get_or_create(
            source_document=src_pn,
            version_label="v1.0",
            defaults={
                "full_text_content": (
                    "Independent dermal irritation testing (Study PN-DERM-42) indicates 99.4% plant-based "
                    "ingredients without artificial fragrances. The formula is hypoallergenic and biodegradable "
                    "within 28 days under OECD 301B guidelines. Cannot claim 100% chemical-free because all matter "
                    "is composed of chemicals."
                ),
                "passage_excerpts": [
                    {
                        "passage_id": "PN-P01",
                        "text": "99.4% plant-based ingredients without artificial fragrances"
                    },
                    {
                        "passage_id": "PN-P02",
                        "text": "Cannot claim 100% chemical-free because all matter is composed of chemicals."
                    }
                ]
            }
        )

        BrandRule.objects.get_or_create(
            workspace=purenest,
            name="Prohibit '100% Chemical-Free'",
            defaults={
                "rule_type": BrandRule.RuleType.PROHIBITED_PHRASE,
                "pattern_or_phrase": "100% chemical-free",
                "preferred_alternative": "99.4% plant-derived ingredients",
                "explanation": "Scientifically inaccurate marketing term; water and plant oils are chemical substances.",
                "severity": BrandRule.Severity.HIGH
            }
        )

        # 7. Populate FinEdge Rules & Sources
        BrandRule.objects.get_or_create(
            workspace=finedge,
            name="No Guaranteed Investment Returns",
            defaults={
                "rule_type": BrandRule.RuleType.PROHIBITED_PHRASE,
                "pattern_or_phrase": "guaranteed returns",
                "preferred_alternative": "historical market performance does not guarantee future results",
                "explanation": "SEC compliance forbids promising guaranteed financial investment returns.",
                "severity": BrandRule.Severity.CRITICAL
            }
        )

        # 8. Add shared review-queue content so reviewer and manager demos are usable.
        demo_item, _ = ContentItem.objects.get_or_create(
            workspace=ecovolt,
            title="EcoVolt Home Energy Copy Review",
            defaults={
                "description": "Fictional demo content for reviewer and account-manager workflows.",
                "created_by": creator_user,
            }
        )
        ContentVersion.objects.get_or_create(
            content_item=demo_item,
            version_number=1,
            defaults={
                "raw_text": (
                    "EcoVolt™ helps make everyday home management simpler. "
                    "Explore practical ideas for a more comfortable home."
                ),
                "status": ContentVersion.Status.SUBMITTED,
                "created_by": creator_user,
            }
        )

        # 9. Log initial Audit Event
        AuditEvent.objects.create(
            workspace=ecovolt,
            user=admin_user,
            event_type=AuditEvent.EventType.RULE_CREATED,
            description="Initial demonstration brand rules and source benchmarks configured for EcoVolt."
        )

        self.stdout.write(self.style.SUCCESS("Successfully seeded fictional demo data!"))
