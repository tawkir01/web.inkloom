import uuid
from django.db import models
from django.conf import settings
from workspaces.models import ClientWorkspace

class AuditEvent(models.Model):
    """
    Append-only compliance audit trail recording all security and governance events.
    Never exposes plain text secrets or passwords.
    """
    class EventType(models.TextChoices):
        CONTENT_SUBMITTED = 'CONTENT_SUBMITTED', 'Content Submitted'
        CONTENT_REVISED = 'CONTENT_REVISED', 'Content Revised (New Version)'
        REVIEW_COMPLETED = 'REVIEW_COMPLETED', 'Automated Review Completed'
        REVIEW_RUN_COMPLETED = 'REVIEW_RUN_COMPLETED', 'Review Run Completed'
        APPROVAL_DECISION_MADE = 'APPROVAL_DECISION_MADE', 'Approval Decision Made'
        APPROVAL_GRANTED = 'APPROVAL_GRANTED', 'Approval Granted'
        APPROVAL_REJECTED = 'APPROVAL_REJECTED', 'Approval Rejected'
        CHANGES_REQUESTED = 'CHANGES_REQUESTED', 'Changes Requested'
        RULE_CREATED = 'RULE_CREATED', 'Brand Rule Created'
        RULE_MODIFIED = 'RULE_MODIFIED', 'Brand Rule Modified'
        SOURCE_ADDED = 'SOURCE_ADDED', 'Source Document Added'
        SOURCE_MODIFIED = 'SOURCE_MODIFIED', 'Source Document Modified'
        MEMBERSHIP_CHANGED = 'MEMBERSHIP_CHANGED', 'Membership or Role Modified'
        ACCESS_DENIED = 'ACCESS_DENIED', 'Security: Cross-Client Access Denied'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(
        ClientWorkspace, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='audit_events'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='triggered_audit_events'
    )
    event_type = models.CharField(
        max_length=64, 
        choices=EventType.choices
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    description = models.TextField(help_text="Detailed audit summary of the action")
    metadata = models.JSONField(
        default=dict, 
        blank=True, 
        help_text="Sanitized contextual information (IDs, version numbers, status transitions)"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['workspace', '-created_at']),
            models.Index(fields=['event_type', '-created_at']),
        ]

    def __str__(self):
        user_str = self.user.username if self.user else "System"
        return f"[{self.created_at.strftime('%Y-%m-%d %H:%M')}] {self.event_type} by {user_str}"
