from rest_framework import serializers
from django.contrib.auth.models import User
from apps.core.models import UserProfile, UsageRecord


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['user_type', 'phone', 'company', 'industry', 'plan', 'max_agents', 'token_quota', 'token_used', 'is_active']


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'date_joined', 'last_login', 'profile']
        read_only_fields = ['id', 'date_joined', 'last_login']


class UsageRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsageRecord
        fields = ['id', 'tokens', 'cost', 'request_count', 'created_at']