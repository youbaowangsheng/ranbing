from rest_framework import serializers
from apps.core.models import AgentConfig


class AgentConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentConfig
        fields = ['id', 'fipai_agent_id', 'agent_name', 'agent_type', 'config', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'fipai_agent_id', 'created_at', 'updated_at']