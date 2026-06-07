from rest_framework import serializers
from django.contrib.auth.models import User
from .models import AgentConfig, UsageRecord, MatchingRecord, PublishTask


class AgentConfigSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = AgentConfig
        fields = ['id', 'user', 'user_username', 'fipai_agent_id', 'agent_name',
                  'agent_type', 'description', 'capabilities', 'config', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class AgentConfigCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentConfig
        fields = ['user', 'fipai_agent_id', 'agent_name', 'agent_type', 'description', 'capabilities', 'config', 'is_active']


class UsageRecordSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    agent_name = serializers.CharField(source='agent.agent_name', read_only=True, allow_null=True)

    class Meta:
        model = UsageRecord
        fields = ['id', 'user', 'username', 'agent', 'agent_name', 'tokens', 'cost', 'request_count', 'created_at']


class MatchingRecordSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    agent_name = serializers.CharField(source='agent.agent_name', read_only=True, allow_null=True)

    class Meta:
        model = MatchingRecord
        fields = ['id', 'user', 'username', 'agent', 'agent_name', 'demand_id', 'supply_id',
                  'match_score', 'status', 'created_at']


class PublishTaskSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    agent_name = serializers.CharField(source='agent.agent_name', read_only=True, allow_null=True)
    platform_display = serializers.CharField(source='get_platform_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = PublishTask
        fields = ['id', 'user', 'username', 'agent', 'agent_name', 'title', 'content',
                  'platform', 'platform_display', 'status', 'status_display',
                  'published_at', 'created_at']
