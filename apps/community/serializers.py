from rest_framework import serializers
from apps.core.models import CommunityPost


class CommunityPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunityPost
        fields = ['id', 'title', 'content', 'status', 'view_count', 'like_count', 'created_at']
        read_only_fields = ['id', 'view_count', 'like_count', 'created_at']