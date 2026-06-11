"""
JWT Authentication for Django REST Framework
"""
import jwt
import time
from datetime import datetime, timezone
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .models import User


class JWTAuthentication(BaseAuthentication):
    """Custom JWT authentication"""

    def authenticate(self, request):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return None

        token = auth_header[7:]
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed(detail={'code': 1001, 'message': '登录已过期，请重新登录'})
        except jwt.InvalidTokenError:
            raise AuthenticationFailed(detail={'code': 1001, 'message': '无效的登录凭证'})

        user_id = payload.get('user_id')
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise AuthenticationFailed(detail={'code': 1001, 'message': '用户不存在'})

        if user.status != 1:
            raise AuthenticationFailed(detail={'code': 1001, 'message': '账号已被封禁'})

        return (user, token)


def generate_access_token(user):
    """生成JWT access token"""
    payload = {
        'user_id': user.id,
        'exp': int(time.time()) + int(settings.JWT_ACCESS_TOKEN_LIFETIME.total_seconds()),
        'iat': int(time.time()),
        'type': 'access',
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def generate_refresh_token(user):
    """生成JWT refresh token"""
    payload = {
        'user_id': user.id,
        'exp': int(time.time()) + int(settings.JWT_REFRESH_TOKEN_LIFETIME.total_seconds()),
        'iat': int(time.time()),
        'type': 'refresh',
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
