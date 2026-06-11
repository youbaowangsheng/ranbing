"""
用户序列化器
"""
import re
from rest_framework import serializers
from .models import User
from .authentication import generate_access_token, generate_refresh_token


class UserSerializer(serializers.ModelSerializer):
    """用户序列化器（公开信息）"""
    phone = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'uuid', 'phone', 'nickname', 'avatar_url', 'is_verified', 'last_login_at', 'email', 'status']

    def get_phone(self, obj):
        if obj.phone:
            return re.sub(r'(\d{3})\d{4}(\d{4})', r'\1****\2', obj.phone)
        return None


class UserLoginSerializer(serializers.Serializer):
    """手机号+验证码登录"""
    phone = serializers.CharField(max_length=20)
    code = serializers.CharField(max_length=6)

    def validate_phone(self, value):
        if not re.match(r'^1[3-9]\d{9}$', value):
            raise serializers.ValidationError('手机号格式不正确')
        return value

    def validate_code(self, value):
        if not re.match(r'^\d{6}$', value):
            raise serializers.ValidationError('验证码为6位数字')
        return value


class UserRegisterSerializer(serializers.Serializer):
    """注册"""
    phone = serializers.CharField(max_length=20)
    code = serializers.CharField(max_length=6)
    nickname = serializers.CharField(max_length=64, required=False, default='')
    wx_openid = serializers.CharField(max_length=128, required=False, default='')

    def validate_phone(self, value):
        if not re.match(r'^1[3-9]\d{9}$', value):
            raise serializers.ValidationError('手机号格式不正确')
        return value


class SendCodeSerializer(serializers.Serializer):
    """发送验证码"""
    phone = serializers.CharField(max_length=20)
    type = serializers.ChoiceField(choices=['login', 'register'])

    def validate_phone(self, value):
        if not re.match(r'^1[3-9]\d{9}$', value):
            raise serializers.ValidationError('手机号格式不正确')
        return value


class TokenResponseSerializer(serializers.Serializer):
    """登录响应"""
    token = serializers.CharField()
    expires_at = serializers.DateTimeField()
    user = UserSerializer()


class UserListSerializer(serializers.ModelSerializer):
    """用户列表序列化器"""
    phone = serializers.SerializerMethodField()
    profile_data = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'uuid', 'phone', 'nickname', 'avatar_url', 'email', 'status', 'is_verified', 'last_login_at', 'created_at', 'profile_data']

    def get_phone(self, obj):
        if obj.phone:
            return re.sub(r'(\d{3})\d{4}(\d{4})', r'\1****\2', obj.phone)
        return None

    def get_profile_data(self, obj):
        try:
            profile = obj.profile
            return {
                'company': profile.company,
                'industry': profile.industry,
                'position': profile.position,
            }
        except Exception:
            return {}
