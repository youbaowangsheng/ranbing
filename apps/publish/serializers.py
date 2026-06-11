from rest_framework import serializers
from apps.core.models import PublishTask


class PublishTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = PublishTask
        fields = ['id', 'title', 'content', 'platform', 'status', 'published_at', 'created_at']
        read_only_fields = ['id', 'status', 'published_at', 'created_at']