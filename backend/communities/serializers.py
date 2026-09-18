"""Communities序列化器"""
from rest_framework import serializers
from .models import Community, CommunityMember, Message


class CommunitySerializer(serializers.ModelSerializer):
    owner = serializers.SerializerMethodField()
    join_status = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()

    class Meta:
        model = Community
        fields = ['uuid', 'name', 'description', 'community_type', 'school',
                  'cover_url', 'member_count', 'owner', 'qr_code_url', 'created_at',
                  'join_status', 'role']

    def get_join_status(self, obj):
        """当前用户是否已加入：1=已加入，0=未加入（前端据此显示按钮）"""
        joined_map = self.context.get('joined_map') or {}
        return 1 if obj.id in joined_map else 0

    def get_role(self, obj):
        """当前用户在社群中的角色：1=成员 2=管理员 3=群主"""
        joined_map = self.context.get('joined_map') or {}
        info = joined_map.get(obj.id)
        return info.get('role') if info else None

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
    # Message 模型只有 id，没有 uuid，用 SerializerMethodField 暴露 id 为 uuid
    uuid = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ['uuid', 'profile', 'content', 'msg_type', 'is_pinned',
                  'like_count', 'ai_signal_type', 'created_at']

    def get_uuid(self, obj):
        return str(obj.id)

    def get_profile(self, obj):
        return {
            'uuid': str(obj.profile.uuid),
            'real_name': obj.profile.real_name,
            'company': obj.profile.company,
            'avatar_url': obj.profile.user.avatar_url,
        }
