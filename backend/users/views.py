"""
用户认证视图 - 小程序版
"""
import time
import random
import redis
import jwt
import datetime
import re
import requests
from django.conf import settings
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from django.contrib.auth import login
from django.utils import timezone

from .models import User
from .serializers import (
    UserSerializer, UserLoginSerializer, UserRegisterSerializer,
    SendCodeSerializer
)
from .authentication import generate_access_token, generate_refresh_token

# 微信小程序凭证（建议通过环境变量设置）
WX_APPID = getattr(settings, 'WX_APPID', '')
WX_APPSECRET = getattr(settings, 'WX_APPSECRET', '')


def get_redis_client():
    try:
        redis_url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
        client = redis.from_url(redis_url, decode_responses=True)
        client.ping()
        return client
    except Exception:
        return None


def get_token_response(user):
    """生成登录成功的 token 响应数据"""
    token = generate_access_token(user)
    expires_at = datetime.datetime.fromtimestamp(
        int(time.time()) + int(settings.JWT_ACCESS_TOKEN_LIFETIME.total_seconds()),
        tz=datetime.timezone.utc
    )
    data = {
        'token': token,
        'expires_at': expires_at.isoformat(),
        'user': UserSerializer(user).data
    }
    if hasattr(settings, 'JWT_REFRESH_TOKEN_LIFETIME'):
        data['refresh_token'] = generate_refresh_token(user)
    return data


class AuthViewSet(viewsets.GenericViewSet):
    """认证相关API"""
    permission_classes = [AllowAny]

    @action(detail=False, methods=['get'])
    def me(self, request):
        """获取当前用户信息"""
        return Response({'code': 0, 'data': UserSerializer(request.user).data})

    def get_serializer_class(self):
        if self.action == 'login':
            return UserLoginSerializer
        elif self.action == 'register':
            return UserRegisterSerializer
        elif self.action == 'send_code':
            return SendCodeSerializer
        return UserSerializer

    @action(detail=False, methods=['post'])
    def send_code(self, request):
        """发送验证码"""
        serializer = SendCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data['phone']
        code_type = serializer.validated_data['type']

        # 生成6位验证码
        code = str(random.randint(100000, 999999))

        # 存储到Redis（5分钟有效）
        r = get_redis_client()
        if r:
            r.setex(f'code:{phone}:{code_type}', 300, code)

        # 真实发送短信
        try:
            from .sms import send_sms
            template_code = getattr(settings, 'ALIYUN_SMS_TEMPLATE_CODE', '')
            sign_name = getattr(settings, 'ALIYUN_SMS_SIGN_NAME', '')
            send_sms(phone, code, template_code or None, sign_name or None)
        except Exception as e:
            print(f'[SMS ERROR] {phone}: {e}')

        return Response({'code': 0, 'message': '验证码已发送'})

    @action(detail=False, methods=['post'])
    def email_login(self, request):
        """邮箱+密码登录（运营控制台用）"""
        email = request.data.get('email', '').strip().lower()
        password = request.data.get('password', '').strip()

        if not email or '@' not in email:
            return Response({'code': 2002, 'message': '邮箱格式不正确'}, status=status.HTTP_400_BAD_REQUEST)
        if not password:
            return Response({'code': 2002, 'message': '请输入密码'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'code': 2001, 'message': '该邮箱未注册'}, status=status.HTTP_400_BAD_REQUEST)
        if not user.check_password(password):
            return Response({'code': 2002, 'message': '密码错误'}, status=status.HTTP_400_BAD_REQUEST)

        user.last_login_at = timezone.now()
        user.save(update_fields=['last_login_at'])

        return Response({'success': True, 'token': get_token_response(user)['token'], 'user': UserSerializer(user).data})

    @action(detail=False, methods=['post'])
    def login(self, request):
        """
        手机号登录（支持密码 或 验证码）
        - 传 password 字段 → 密码登录
        - 传 code 字段 → 短信登录
        """
        phone = request.data.get('phone', '').strip()
        password = request.data.get('password', '').strip()
        code = request.data.get('code', '').strip()

        if not phone or not re.match(r'^1[3-9]\d{9}$', phone):
            return Response({'code': 2002, 'message': '手机号格式不正确'}, status=status.HTTP_400_BAD_REQUEST)

        # 密码登录
        if password:
            try:
                user = User.objects.get(phone=phone)
            except User.DoesNotExist:
                return Response({'code': 2001, 'message': '该手机号未注册'}, status=status.HTTP_400_BAD_REQUEST)
            if not user.check_password(password):
                return Response({'code': 2002, 'message': '密码错误'}, status=status.HTTP_400_BAD_REQUEST)
        # 短信登录
        elif code:
            r = get_redis_client()
            if r:
                stored_code = r.get(f'code:{phone}:login')
                if stored_code and stored_code != code:
                    return Response({'code': 2002, 'message': '验证码错误'}, status=status.HTTP_400_BAD_REQUEST)
                r.delete(f'code:{phone}:login')
            try:
                user = User.objects.get(phone=phone)
            except User.DoesNotExist:
                return Response({'code': 2001, 'message': '该手机号未注册'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'code': 2002, 'message': '请传密码或验证码'}, status=status.HTTP_400_BAD_REQUEST)

        user.last_login_at = timezone.now()
        user.save(update_fields=['last_login_at'])
        login(request, user)

        return Response({'code': 0, 'data': get_token_response(user)})

    @action(detail=False, methods=['post'])
    def wx_login(self, request):
        """
        微信登录：小程序传 code → 后端换 openid → 返回 token
        """
        code = request.data.get('code', '').strip()
        if not code:
            return Response({'code': 2002, 'message': '缺少code参数'}, status=status.HTTP_400_BAD_REQUEST)

        # 用 code 换 openid
        wx_url = 'https://api.weixin.qq.com/sns/jscode2session'
        try:
            wx_resp = requests.get(wx_url, params={
                'appid': WX_APPID,
                'secret': WX_APPSECRET,
                'js_code': code,
                'grant_type': 'authorization_code'
            }, timeout=5)
            wx_data = wx_resp.json()
            if wx_data.get('errcode'):
                return Response({'code': 3001, 'message': f'微信登录失败: {wx_data.get("errmsg")}'}, status=status.HTTP_400_BAD_REQUEST)
            openid = wx_data.get('openid', '')
        except Exception as e:
            return Response({'code': 3001, 'message': '微信服务不可用'}, status=status.HTTP_400_BAD_REQUEST)

        # 查找或创建用户
        user, created = User.objects.get_or_create(
            wx_openid=openid,
            defaults={'nickname': f'微信用户{openid[-4:]}'}
        )
        user.last_login_at = timezone.now()
        user.save(update_fields=['last_login_at'])

        resp_data = get_token_response(user)
        resp_data['is_new_user'] = created

        return Response({'code': 0, 'data': resp_data})

    @action(detail=False, methods=['post'])
    def register(self, request):
        """注册账号"""
        serializer = UserRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data['phone']
        code = serializer.validated_data['code']
        nickname = serializer.validated_data.get('nickname', f'用户{phone[-4:]}')
        wx_openid = serializer.validated_data.get('wx_openid', '')

        # 验证验证码
        r = get_redis_client()
        if r:
            stored_code = r.get(f'code:{phone}:register')
            if stored_code and stored_code != code:
                return Response({'code': 2002, 'message': '验证码错误'}, status=status.HTTP_400_BAD_REQUEST)

        # 检查是否已注册
        if User.objects.filter(phone=phone).exists():
            return Response({'code': 2003, 'message': '该手机号已注册，请直接登录'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(
            phone=phone,
            nickname=nickname,
            wx_openid=wx_openid
        )

        return Response({'code': 0, 'data': get_token_response(user)}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def email_register(self, request):
        """邮箱注册（运营控制台用）"""
        email = request.data.get('email', '').strip().lower()
        password = request.data.get('password', '').strip()
        nickname = request.data.get('nickname', f'用户{email.split("@")[0][:4]}')

        if not email or '@' not in email:
            return Response({'code': 2002, 'message': '邮箱格式不正确'}, status=status.HTTP_400_BAD_REQUEST)
        if not password or len(password) < 6:
            return Response({'code': 2002, 'message': '密码至少6位'}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=email).exists():
            return Response({'code': 2003, 'message': '该邮箱已注册'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(
            email=email,
            password=password,
            nickname=nickname
        )

        return Response({'success': True, 'token': get_token_response(user)['token'], 'user': UserSerializer(user).data}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def refresh_token(self, request):
        """刷新 access_token"""
        refresh_token_str = request.data.get('refresh_token', '').strip()
        if not refresh_token_str:
            return Response({'code': 2002, 'message': '缺少refresh_token'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            payload = jwt.decode(refresh_token_str, settings.SECRET_KEY, algorithms=['HS256'])
            user = User.objects.get(id=payload['user_id'])
        except (jwt.ExpiredSignatureError, User.DoesNotExist):
            return Response({'code': 1001, 'message': 'refresh_token无效或已过期'}, status=status.HTTP_401_UNAUTHORIZED)

        return Response({'code': 0, 'data': get_token_response(user)})


class UserMeView(APIView):
    """获取当前用户"""

    def get(self, request):
        return Response({
            'code': 0,
            'data': UserSerializer(request.user).data
        })
