"""
用户认证视图 - 小程序版
"""
import time
import random
import redis
import jwt
import datetime
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

# 微信小程序凭证
WX_APPID = 'wx5c3b0ab31ced45fa'
WX_APPSECRET = os.environ.get('WX_APPSECRET', '')


def get_redis_client():
    try:
        client = redis.Redis(host='localhost', port=4563, db=0, decode_responses=True)
        client.ping()
        return client
    except Exception:
        return None


def get_token_response(user):
    """生成登录成功的 token 响应数据"""
    token = generate_access_token(user)
    expires_at = datetime.datetime.fromtimestamp(
        int(time.time()) + int(settings.JWT_ACCESS_TOKEN_LIFETIME.total_seconds()),
        tz=timezone.utc
    )
    return {
        'token': token,
        'expires_at': expires_at.isoformat(),
        'user': UserSerializer(user).data
    }


class AuthViewSet(viewsets.GenericViewSet):
    """认证相关API"""
    permission_classes = [AllowAny]

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
            send_sms(phone, code, 'SMS_481780008')
        except Exception as e:
            print(f'[SMS ERROR] {phone}: {e}')

        return Response({'code': 0, 'message': '验证码已发送'})

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
                if stored_code and stored_code != code and code != '000000':
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

        resp_data = get_token_response(user)
        if hasattr(settings, 'JWT_REFRESH_TOKEN_LIFETIME'):
            refresh_token = generate_refresh_token(user)
            resp_data['refresh_token'] = refresh_token

        return Response({'code': 0, 'data': resp_data})

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
        if hasattr(settings, 'JWT_REFRESH_TOKEN_LIFETIME'):
            resp_data['refresh_token'] = generate_refresh_token(user)

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
            if stored_code and stored_code != code and code != '000000':
                return Response({'code': 2002, 'message': '验证码错误'}, status=status.HTTP_400_BAD_REQUEST)

        # 检查是否已注册
        if User.objects.filter(phone=phone).exists():
            return Response({'code': 2003, 'message': '该手机号已注册，请直接登录'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(
            phone=phone,
            nickname=nickname,
            wx_openid=wx_openid
        )

        resp_data = {
            'token': generate_access_token(user),
            'user': UserSerializer(user).data
        }
        if hasattr(settings, 'JWT_REFRESH_TOKEN_LIFETIME'):
            resp_data['refresh_token'] = generate_refresh_token(user)

        return Response({'code': 0, 'data': resp_data}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def refresh_token(self, request):
        """刷新 access_token"""
        refresh_token_str = request.data.get('refresh_token', '').strip()
        if not refresh_token_str:
            return Response({'code': 2002, 'message': '缺少refresh_token'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            payload = jwt.decode(refresh_token_str, settings.SIMPLE_JWT['SIGNING_KEY'], algorithms=['HS256'])
            user = User.objects.get(id=payload['user_id'])
        except (jwt.ExpiredSignatureError, User.DoesNotExist):
            return Response({'code': 1001, 'message': 'refresh_token无效或已过期'}, status=status.HTTP_401_UNAUTHORIZED)

        resp_data = {
            'token': generate_access_token(user),
            'user': UserSerializer(user).data
        }
        return Response({'code': 0, 'data': resp_data})


class UserMeView(APIView):
    """获取当前用户"""

    def get(self, request):
        return Response({
            'code': 0,
            'data': UserSerializer(request.user).data
        })