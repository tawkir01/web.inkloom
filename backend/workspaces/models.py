import uuid
from django.db import models
from django.conf import settings
from django.utils.text import slugify

class Organisation(models.Model):
    """
    Stores top-level enterprise marketing agency or corporate organization.
    All client workspaces belong to an organisation.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Organisation'
        verbose_name_plural = 'Organisations'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ClientWorkspace(models.Model):
    """
    Represents an isolated brand workspace (e.g. EcoVolt, PureNest, FinEdge).
    Enforces tenant boundaries: every rule, source, and review is bounded by workspace.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organisation = models.ForeignKey(
        Organisation, 
        on_delete=models.CASCADE, 
        related_name='workspaces'
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, blank=True)
    industry = models.CharField(max_length=128, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        unique_together = ('organisation', 'slug')
        indexes = [
            models.Index(fields=['organisation', 'slug']),
            models.Index(fields=['is_active']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.organisation.name})"


class WorkspaceMembership(models.Model):
    """
    Connects a User to a ClientWorkspace with a strictly enforced role:
    - Agency Administrator: Configures rules, sources, memberships
    - Content Creator: Submits copy and media, accepts revisions
    - Account Manager: Coordinates client reviews and revision requests
    - Brand Reviewer: Holds exclusive rights to approve or reject exact version snapshots
    """
    class Role(models.TextChoices):
        ADMIN = 'AGENCY_ADMIN', 'Agency Administrator'
        CREATOR = 'CONTENT_CREATOR', 'Content Creator'
        MANAGER = 'ACCOUNT_MANAGER', 'Account Manager'
        REVIEWER = 'BRAND_REVIEWER', 'Brand Reviewer'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(
        ClientWorkspace, 
        on_delete=models.CASCADE, 
        related_name='memberships'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='workspace_memberships'
    )
    role = models.CharField(
        max_length=32, 
        choices=Role.choices, 
        default=Role.CREATOR
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('workspace', 'user', 'role')
        indexes = [
            models.Index(fields=['workspace', 'user']),
            models.Index(fields=['role']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()} @ {self.workspace.name}"
