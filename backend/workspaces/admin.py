from django.contrib import admin
from .models import Organisation, ClientWorkspace, WorkspaceMembership

@admin.register(Organisation)
class OrganisationAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(ClientWorkspace)
class ClientWorkspaceAdmin(admin.ModelAdmin):
    list_display = ('name', 'organisation', 'industry', 'is_active', 'created_at')
    list_filter = ('organisation', 'is_active', 'industry')
    search_fields = ('name', 'industry', 'description')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(WorkspaceMembership)
class WorkspaceMembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'workspace', 'role', 'is_active', 'created_at')
    list_filter = ('role', 'is_active', 'workspace')
    search_fields = ('user__username', 'user__email', 'workspace__name')
