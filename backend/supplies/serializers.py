"""Supplies序列化器"""
from rest_framework import serializers
from .models import Supply, Match, Connection, Followup, FriendRequest, Card


class ProfileMiniSerializer(serializers.Serializer):
    """精简Profile信息"""
    uuid = serializers.UUIDField()
    real_name = serializers.CharField()
    company = serializers.CharField()
    position = serializers.CharField()
    cert_level = serializers.IntegerField()
    avatar_url = serializers.SerializerMethodField()

    def get_avatar_url(self, obj):
        # obj is Profile, get avatar from user
        if hasattr(obj, 'user') and obj.user:
            return obj.user.avatar_url or ''
        return ''


class TagMiniSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()


class SupplyListSerializer(serializers.ModelSerializer):
    """供需列表"""
    profile = ProfileMiniSerializer(read_only=True)
    tags = serializers.SerializerMethodField()
    is_mine = serializers.SerializerMethodField()

    class Meta:
        model = Supply
        fields = ['uuid', 'profile', 'supply_type', 'title', 'content',
                  'tags', 'match_count', 'view_count', 'quality_score',
                  'status', 'created_at', 'is_mine']

    def get_tags(self, obj):
        # obj.tags is JSONField: [{id, name}, ...] or [id, ...]
        if not obj.tags:
            return []
        result = []
        for t in obj.tags:
            if isinstance(t, dict):
                result.append({'id': t.get('id'), 'name': t.get('name')})
            elif isinstance(t, int):
                result.append({'id': t, 'name': None})
        return result

    def get_is_mine(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            return obj.profile.user_id == request.user.id
        return False


class SupplyDetailSerializer(serializers.ModelSerializer):
    profile = ProfileMiniSerializer(read_only=True)
    tags = serializers.SerializerMethodField()

    class Meta:
        model = Supply
        fields = ['uuid', 'profile', 'supply_type', 'title', 'content', 'tags',
                  'view_count', 'match_count', 'quality_score', 'status',
                  'created_at', 'expires_at']

    def get_tags(self, obj):
        if not obj.tags:
            return []
        result = []
        for t in obj.tags:
            if isinstance(t, dict):
                result.append({'id': t.get('id'), 'name': t.get('name')})
            elif isinstance(t, int):
                result.append({'id': t, 'name': None})
        return result


class SupplyCreateSerializer(serializers.Serializer):
    supply_type = serializers.IntegerField(min_value=1, max_value=2)
    title = serializers.CharField(max_length=256)
    content = serializers.CharField(required=False, default='')
    tags = serializers.ListField(child=serializers.IntegerField(), required=False, default=list)


class SupplyFeedSerializer(serializers.ModelSerializer):
    profile = ProfileMiniSerializer(read_only=True)
    match_score = serializers.FloatField(read_only=True)
    match_reason = serializers.CharField(read_only=True, required=False)

    class Meta:
        model = Supply
        fields = ['uuid', 'profile', 'supply_type', 'title', 'tags',
                  'match_score', 'match_reason', 'created_at']


class MatchSerializer(serializers.ModelSerializer):
    profile = ProfileMiniSerializer(source='target_profile', read_only=True)

    class Meta:
        model = Match
        fields = ['uuid', 'profile', 'match_score', 'ai_reason',
                  'status', 'push_status', 'feedback_score', 'created_at']


class ConnectionSerializer(serializers.ModelSerializer):
    profile = ProfileMiniSerializer(source='user_b.profile', read_only=True)

    class Meta:
        model = Connection
        fields = ['uuid', 'profile', 'conn_type', 'relation_strength',
                  'last_interact_at', 'interact_count', 'is_mutual', 'status']


class FollowupSerializer(serializers.ModelSerializer):
    to_profile = ProfileMiniSerializer(read_only=True)

    class Meta:
        model = Followup
        fields = ['uuid', 'to_profile', 'trigger_event', 'ai_script',
                  'followup_type', 'scheduled_at', 'sent_at', 'status']


class FriendRequestSerializer(serializers.ModelSerializer):
    from_profile = ProfileMiniSerializer(read_only=True)
    to_profile = ProfileMiniSerializer(read_only=True)

    class Meta:
        model = FriendRequest
        fields = ['uuid', 'from_profile', 'to_profile', 'message',
                  'status', 'created_at']


class CardSerializer(serializers.ModelSerializer):
    owner = ProfileMiniSerializer(read_only=True)

    class Meta:
        model = Card
        fields = ['uuid', 'owner', 'title', 'bio', 'show_company', 'show_position',
                  'show_education', 'show_tags', 'show_contact', 'style_config',
                  'view_count', 'status', 'created_at', 'updated_at']
        read_only_fields = ['view_count', 'created_at', 'updated_at']


class CardDetailSerializer(serializers.ModelSerializer):
    """名片详情（含关联的profile信息）"""
    profile = serializers.SerializerMethodField()

    class Meta:
        model = Card
        fields = ['uuid', 'profile', 'title', 'bio', 'show_company', 'show_position',
                  'show_education', 'show_tags', 'show_contact', 'style_config',
                  'view_count', 'status', 'created_at', 'updated_at']

    def get_profile(self, obj):
        from .serializers import ProfileMiniSerializer
        return ProfileMiniSerializer(obj.owner).data
