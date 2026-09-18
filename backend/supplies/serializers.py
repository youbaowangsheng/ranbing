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
                  'status', 'audit_status', 'created_at', 'is_mine']

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
    images = serializers.ListField(child=serializers.CharField(), required=False, default=list)

    def to_internal_value(self, data):
        # 容错：前端可能传 [null] 或 ['26']，这里统一过滤成有效的 int 列表，
        # 避免因个别脏值导致整个发布请求 400
        mutable = data.copy() if hasattr(data, 'copy') else dict(data)
        raw_tags = mutable.get('tags')
        if isinstance(raw_tags, list):
            cleaned = []
            for t in raw_tags:
                try:
                    v = int(t)
                    if v > 0:
                        cleaned.append(v)
                except (TypeError, ValueError):
                    continue
            mutable['tags'] = cleaned
        return super().to_internal_value(mutable)


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
    profile = serializers.SerializerMethodField()

    class Meta:
        model = Connection
        fields = ['uuid', 'profile', 'conn_type', 'relation_strength',
                  'last_interact_at', 'interact_count', 'is_mutual', 'status']

    def get_profile(self, obj):
        """动态取"对方"的 profile（Connection 按 id 排序 user_a < user_b）"""
        request = self.context.get('request')
        current_user = getattr(request, 'user', None) if request else None

        # 无 context 时默认返回 user_b（向后兼容）
        if not current_user or not current_user.is_authenticated:
            target_user = obj.user_b
        elif obj.user_a_id == current_user.id:
            target_user = obj.user_b
        else:
            target_user = obj.user_a

        profile = getattr(target_user, 'profile', None)
        if not profile:
            return None
        return ProfileMiniSerializer(profile).data


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
        fields = ['uuid', 'owner',
                  # 名片内容（小程序编辑页用）
                  'name', 'company', 'position', 'phone', 'wechat', 'email',
                  'tags', 'is_default', 'visibility',
                  # 展示配置
                  'title', 'bio', 'show_company', 'show_position',
                  'show_education', 'show_tags', 'show_contact', 'style_config',
                  'view_count', 'status', 'created_at', 'updated_at']
        read_only_fields = ['view_count', 'created_at', 'updated_at']


class CardDetailSerializer(serializers.ModelSerializer):
    """名片详情（含关联的 profile 信息）"""
    profile = serializers.SerializerMethodField()

    class Meta:
        model = Card
        fields = ['uuid', 'profile',
                  # 名片内容（小程序展示/编辑页用）
                  'name', 'company', 'position', 'phone', 'wechat', 'email',
                  'tags', 'is_default', 'visibility',
                  # 展示配置
                  'title', 'bio', 'show_company', 'show_position',
                  'show_education', 'show_tags', 'show_contact', 'style_config',
                  'view_count', 'status', 'created_at', 'updated_at']

    def get_profile(self, obj):
        return ProfileMiniSerializer(obj.owner).data
