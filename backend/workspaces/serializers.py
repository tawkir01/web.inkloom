from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Organisation, ClientWorkspace, WorkspaceMembership

User = get_user_model()

class UserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'full_name', 'is_staff']

    def get_full_name(self, obj):
        name = f"{obj.first_name} {obj.last_name}".strip()
        return name if name else obj.username


class WorkspaceMembershipSummarySerializer(serializers.ModelSerializer):
    workspace_id = serializers.UUIDField(source='workspace.id', read_only=True)
    workspace_name = serializers.CharField(source='workspace.name', read_only=True)
    workspace_slug = serializers.CharField(source='workspace.slug', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = WorkspaceMembership
        fields = ['id', 'workspace_id', 'workspace_name', 'workspace_slug', 'role', 'role_display', 'is_active']


class ClientWorkspaceSerializer(serializers.ModelSerializer):
    organisation_name = serializers.CharField(source='organisation.name', read_only=True)
    user_roles = serializers.SerializerMethodField()
    rules_count = serializers.SerializerMethodField()
    claims_count = serializers.SerializerMethodField()
    sources_count = serializers.SerializerMethodField()

    class Meta:
        model = ClientWorkspace
        fields = [
            'id', 'organisation', 'organisation_name', 'name', 'slug',
            'industry', 'description', 'is_active', 'user_roles',
            'rules_count', 'claims_count', 'sources_count', 'created_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at']

    def get_user_roles(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return []
        memberships = obj.memberships.filter(user=request.user, is_active=True)
        return [m.role for m in memberships]

    def get_rules_count(self, obj):
        return obj.brand_rules.filter(is_active=True).count()

    def get_claims_count(self, obj):
        return obj.approved_claims.filter(is_active=True).count()

    def get_sources_count(self, obj):
        return obj.source_documents.count()


class WorkspaceMemberDetailSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), 
        source='user', 
        write_only=True
    )
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = WorkspaceMembership
        fields = ['id', 'user', 'user_id', 'role', 'role_display', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']
