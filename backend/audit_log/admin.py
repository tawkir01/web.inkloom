from django.contrib import admin
from .models import AuditEvent

@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'event_type', 'user', 'workspace', 'ip_address')
    list_filter = ('event_type', 'workspace')
    search_fields = ('description', 'user__username', 'ip_address')
    readonly_fields = ('id', 'created_at', 'event_type', 'user', 'workspace', 'ip_address', 'description', 'metadata')

    def has_add_permission(self, request):
        # Audit events are append-only by the system, never manually created in admin
        return False

    def has_delete_permission(self, request, obj=None):
        # Prevent tampering with audit logs
        return False
