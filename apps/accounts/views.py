from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Count
from django.utils import timezone
from apps.core.models import UserProfile, UsageRecord
from .serializers import AccountProfileSerializer, UsageRecordSerializer


class AccountViewSet(viewsets.ViewSet):
    """账户管理 API"""

    @action(detail=False, methods=['get', 'put'])
    def profile(self, request):
        """获取/更新当前用户的账户信息"""
        user = request.user
        if not user.is_authenticated:
            return Response({'error': '未登录'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            profile = user.profile
        except UserProfile.DoesNotExist:
            profile = UserProfile.objects.create(user=user)

        if request.method == 'GET':
            serializer = AccountProfileSerializer(profile)
            return Response(serializer.data)

        # PUT - 更新
        serializer = AccountProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def usage(self, request):
        """获取当前用户的用量统计"""
        user = request.user
        if not user.is_authenticated:
            return Response({'error': '未登录'}, status=status.HTTP_401_UNAUTHORIZED)

        # 时间范围
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timezone.timedelta(days=days)

        records = UsageRecord.objects.filter(user=user, created_at__gte=start_date)
        stats = records.aggregate(
            total_tokens=Sum('tokens'),
            total_cost=Sum('cost'),
            total_requests=Sum('request_count')
        )

        return Response({
            'period_days': days,
            'total_tokens': stats['total_tokens'] or 0,
            'total_cost': float(stats['total_cost'] or 0),
            'total_requests': stats['total_requests'] or 0,
        })

    @action(detail=False, methods=['get'])
    def quota(self, request):
        """获取当前用户的配额信息"""
        user = request.user
        if not user.is_authenticated:
            return Response({'error': '未登录'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            profile = user.profile
        except UserProfile.DoesNotExist:
            profile = UserProfile.objects.create(user=user)

        return Response({
            'plan': profile.plan,
            'max_agents': profile.max_agents,
            'token_quota': profile.token_quota,
            'token_used': profile.token_used,
            'token_remaining': profile.token_quota - profile.token_used,
        })