from rest_framework import serializers
from apps.core.models import UserProfile, UsageRecord


class AccountProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = UserProfile
        fields = ['username', 'email', 'phone', 'company', 'industry', 'plan', 'max_agents', 'token_quota', 'token_used', 'is_active']
        read_only_fields = ['username', 'email', 'plan', 'max_agents', 'token_quota', 'token_used']


class UsageRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsageRecord
        fields = ['id', 'tokens', 'cost', 'request_count', 'created_at']