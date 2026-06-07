"""Communities序列化器"""
from rest_framework import serializers
from .models import Community, CommunityMember, Message


class CommunitySerializer(serializers.ModelSerializer):
    owner = serializers.SerializerMethodField()

    class Meta:
        model = Community
        fields = ['uuid', 'name', 'description', 'community_type', 'school',
                  'cover_url', 'member_count', 'owner', 'qr_code_url', 'created_at']

    def get_owner(self, obj):
        if hasattr(obj, 'owner') and obj.owner:
            return {
                'uuid': str(obj.owner.uuid),
                'real_name': obj.owner.real_name,
                'company': obj.owner.company,
                'avatar_url': obj.owner.user.avatar_url if hasattr(obj.owner, 'user') else '',
            }
        return None


class MessageSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ['uuid', 'profile', 'content', 'msg_type', 'is_pinned',
                  'like_count', 'ai_signal_type', 'created_at']

    def get_profile(self, obj):
        return {
            'uuid': str(obj.profile.uuid),
            'real_name': obj.profile.real_name,
            'company': obj.profile.company,
            'avatar_url': obj.profile.user.avatar_url,
        }
