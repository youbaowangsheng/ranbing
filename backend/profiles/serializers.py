"""Profile序列化器"""
from rest_framework import serializers
from .models import Profile, ProfileTag, Tag, PrivateMessage


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'l1_category', 'tag_type']


class ProfileTagSerializer(serializers.ModelSerializer):
    tag = TagSerializer(read_only=True)
    tag_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = ProfileTag
        fields = ['id', 'tag', 'tag_id', 'tag_type', 'weight', 'is_ai_ext']


class ProfileListSerializer(serializers.ModelSerializer):
    """Profile列表（精简版）"""
    tags = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = ['uuid', 'real_name', 'company', 'position', 'industry',
                  'city', 'cert_level', 'conn_count', 'tags']

    def get_tags(self, obj):
        return list(obj.profile_tags.select_related('tag').values(
            'tag_id', tag_name='tag__name', tag_type='tag_type', weight='weight'))


class ProfileDetailSerializer(serializers.ModelSerializer):
    """Profile详情"""
    tags = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = ['uuid', 'real_name', 'gender', 'company', 'position',
                  'industry', 'city', 'bio', 'education_year', 'education_major',
                  'education_school', 'cert_level', 'conn_count', 'active_score',
                  'last_active_at', 'tags']

    def get_tags(self, obj):
        pts = obj.profile_tags.select_related('tag').all()
        return [{'id': pt.tag_id, 'name': pt.tag.name, 'tag_type': pt.tag_type, 'weight': float(pt.weight)} for pt in pts]


class ProfileEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['real_name', 'gender', 'birthday', 'company', 'position',
                  'industry', 'city', 'bio', 'education_year', 'education_major',
                  'education_school']


class CertSubmitSerializer(serializers.Serializer):
    cert_level = serializers.IntegerField(min_value=1, max_value=3)
    education_year = serializers.CharField(max_length=10, required=False)
    education_school = serializers.CharField(max_length=128, required=False)
    education_major = serializers.CharField(max_length=128, required=False)
    cert_document_url = serializers.URLField(required=False, default='')


class ProfileTagsUpdateSerializer(serializers.Serializer):
    tags = serializers.ListField(child=serializers.DictField(), min_length=1)

    def validate_tags(self, value):
        for item in value:
            if 'id' not in item or 'tag_type' not in item:
                raise serializers.ValidationError('每个标签需包含id和tag_type')
        return value


class PrivateMessageSerializer(serializers.ModelSerializer):
    from_profile = ProfileListSerializer(read_only=True)
    to_profile = ProfileListSerializer(read_only=True)

    class Meta:
        model = PrivateMessage
        fields = ['uuid', 'from_profile', 'to_profile', 'content', 'is_read', 'created_at']


class ConversationSerializer(serializers.Serializer):
    """会话列表（每个好友一条，按最新消息时间排序）"""
    peer = ProfileListSerializer()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.IntegerField()

    def get_last_message(self, obj):
        return PrivateMessageSerializer(obj['last_message']).data if obj.get('last_message') else None
