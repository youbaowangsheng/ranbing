from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.db.models import Count
from apps.core.models import UserProfile, UsageRecord
from .serializers import UserSerializer, UserProfileSerializer


class UserViewSet(viewsets.ModelViewSet):
    """用户管理 API"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['username', 'email']
    ordering_fields = ['date_joined', 'last_login']

    def get_queryset(self):
        """支持租户过滤（如果需要）"""
        tenant_id = self.request.headers.get('X-Tenant-Id')
        if tenant_id:
            return User.objects.filter(userprofile__id=int(tenant_id))
        return User.objects.all()

    def retrieve(self, request, *args, **kwargs):
        """获取用户详情，包含profile和统计"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data

        # 添加扩展信息
        try:
            profile = instance.profile
            data['profile'] = UserProfileSerializer(profile).data
        except UserProfile.DoesNotExist:
            data['profile'] = None

        # 用量统计
        stats = UsageRecord.objects.filter(user=instance).aggregate(
            total_tokens=Count('id'),
            total_cost=Count('tokens')
        )
        data['usage_stats'] = {
            'total_requests': stats['total_tokens'] or 0,
            'total_cost': float(stats['total_cost'] or 0),
        }

        return Response(data)

    @action(detail=True, methods=['post'])
    def disable(self, request, pk=None):
        """禁用/启用用户"""
        user = self.get_object()
        is_disable = request.data.get('disable', True)

        try:
            profile = user.profile
            profile.is_active = not is_disable
            profile.save()
        except UserProfile.DoesNotExist:
            UserProfile.objects.create(user=user, is_active=not is_disable)

        return Response({'status': 'success', 'is_active': not is_disable})

    @action(detail=True, methods=['post'])
    def set_user_type(self, request, pk=None):
        """设置用户类型"""
        user = self.get_object()
        user_type = request.data.get('user_type', 'regular')

        if user_type not in ['admin', 'superuser', 'regular']:
            return Response({'success': False, 'error': '无效的用户类型'}, status=400)

        try:
            profile = user.profile
            profile.user_type = user_type
            profile.save()
        except UserProfile.DoesNotExist:
            UserProfile.objects.create(user=user, user_type=user_type)

        return Response({'success': True})

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """用户统计汇总"""
        total = User.objects.count()
        active = User.objects.filter(profile__is_active=True).count()
        new_today = User.objects.filter(date_joined__date__exact=True).count()
        return Response({
            'total': total,
            'active': active,
            'new_today': new_today,
        })