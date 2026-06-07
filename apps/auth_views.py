"""
Console 运营后台认证 API - 简单 Token 验证
"""
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(['POST'])
def login(request):
    """邮箱密码登录"""
    email = request.data.get('email', '')
    password = request.data.get('password', '')

    if not email or not password:
        return Response({'success': False, 'error': '请输入邮箱和密码'})

    try:
        user_obj = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({'success': False, 'error': '用户不存在'})

    user = authenticate(username=user_obj.username, password=password)
    if user is None:
        return Response({'success': False, 'error': '密码错误'})

    if not user.is_active:
        return Response({'success': False, 'error': '账号已被禁用'})

    # 获取用户类型
    try:
        user_type = user.profile.user_type
    except:
        user_type = 'regular'

    import time
    token = f"console_{user.id}_{int(time.time())}"

    return Response({
        'success': True,
        'token': token,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_staff': user.is_staff,
            'user_type': user_type,
        }
    })


@api_view(['POST'])
def logout(request):
    return Response({'success': True})


@api_view(['GET'])
def userinfo(request):
    """验证 token 并返回用户信息"""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return Response({'success': False, 'error': '未登录'}, status=401)

    token = auth_header[7:]
    if not token.startswith('console_'):
        return Response({'success': False, 'error': '无效token'}, status=401)

    try:
        parts = token.split('_')
        user_id = int(parts[1])
        user = User.objects.get(id=user_id)
    except (ValueError, IndexError, User.DoesNotExist):
        return Response({'success': False, 'error': '无效token'}, status=401)

    try:
        user_type = user.profile.user_type
    except:
        user_type = 'regular'

    return Response({
        'success': True,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_staff': user.is_staff,
            'user_type': user_type,
        }
    })


@api_view(['POST'])
def register(request):
    email = request.data.get('email', '')
    password = request.data.get('password', '')
    name = request.data.get('name', '')
    user_type = request.data.get('user_type', 'regular')

    if not email or not password:
        return Response({'success': False, 'error': '请输入邮箱和密码'})

    if User.objects.filter(email=email).exists():
        return Response({'success': False, 'error': '邮箱已被注册'})

    user = User.objects.create_user(
        username=email.split('@')[0],
        email=email,
        password=password,
        first_name=name
    )

    # 设置用户类型
    UserProfile = User.profile.field.related_model
    UserProfile.objects.create(user=user, user_type=user_type)

    return Response({'success': True})