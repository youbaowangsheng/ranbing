from rest_framework import serializers
from apps.core.models import MatchingRecord


class MatchingRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = MatchingRecord
        fields = ['id', 'demand_id', 'supply_id', 'match_score', 'status', 'created_at']
        read_only_fields = ['id', 'match_score', 'created_at']