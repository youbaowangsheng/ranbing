from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from datetime import timedelta
from apps.core.models import UsageRecord, AgentConfig
from apps.admin_client import get_admin_client


class StatsViewSet(viewsets.ViewSet):
    """运营统计 API"""

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Dashboard 汇总数据"""
        user = request.user
        if not user.is_authenticated:
            return Response({'error': '未登录'}, status=401)

        # 今日数据
        today = timezone.now().date()
        today_start = timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.min.time()))

        today_stats = UsageRecord.objects.filter(
            user=user,
            created_at__gte=today_start
        ).aggregate(
            tokens=Sum('tokens'),
            requests=Sum('request_count'),
            cost=Sum('cost')
        )

        # Agent 数量
        agent_count = AgentConfig.objects.filter(user=user).count()
        active_agents = AgentConfig.objects.filter(user=user, is_active=True).count()

        # 配额信息
        try:
            profile = user.profile
            token_quota = profile.token_quota
            token_used = profile.token_used
        except:
            token_quota = 100000
            token_used = 0

        return Response({
            'today': {
                'tokens': today_stats['tokens'] or 0,
                'requests': today_stats['requests'] or 0,
                'cost': float(today_stats['cost'] or 0),
            },
            'agents': {
                'total': agent_count,
                'active': active_agents,
            },
            'quota': {
                'total': token_quota,
                'used': token_used,
                'remaining': token_quota - token_used,
            }
        })

    @action(detail=False, methods=['get'])
    def daily(self, request):
        """每日趋势数据"""
        user = request.user
        if not user.is_authenticated:
            return Response({'error': '未登录'}, status=401)

        days = int(request.query_params.get('days', 7))
        start_date = timezone.now() - timedelta(days=days)

        # 按日期分组统计
        daily_stats = UsageRecord.objects.filter(
            user=user,
            created_at__gte=start_date
        ).extra(select={'day': "date(created_at)"}).values('day').annotate(
            tokens=Sum('tokens'),
            requests=Sum('request_count'),
            cost=Sum('cost')
        ).order_by('day')

        return Response(list(daily_stats))

    @action(detail=False, methods=['get'])
    def usage(self, request):
        """用量报表（分页）"""
        user = request.user
        if not user.is_authenticated:
            return Response({'error': '未登录'}, status=401)

        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)

        records = UsageRecord.objects.filter(
            user=user,
            created_at__gte=start_date
        ).select_related('agent').order_by('-created_at')

        # 手动分页
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        start = (page - 1) * page_size
        end = start + page_size

        total = records.count()
        data = list(records[start:end].values(
            'id', 'tokens', 'cost', 'request_count', 'created_at',
            agent_name='agent__agent_name'
        ))

        return Response({
            'total': total,
            'page': page,
            'page_size': page_size,
            'results': data
        })

    @action(detail=False, methods=['get'])
    def agents_rank(self, request):
        """Agent使用排行"""
        user = request.user
        if not user.is_authenticated:
            return Response({'error': '未登录'}, status=401)

        # 按Agent分组统计
        agent_stats = UsageRecord.objects.filter(
            user=user
        ).values('agent__agent_name').annotate(
            total_tokens=Sum('tokens'),
            total_requests=Sum('request_count'),
            total_cost=Sum('cost')
        ).order_by('-total_tokens')[:10]

        return Response(list(agent_stats))

    @action(detail=False, methods=['get'])
    def content(self, request):
        """内容统计 - 各模块审核情况"""
        admin_client = get_admin_client()

        # 活动统计
        activities_res = admin_client.get_activities_all(1, 1)
        pending_activities = admin_client.get_activities_pending(1, 1)

        # 社群统计
        communities_res = admin_client.get_communities_pending(1, 1)

        # 供需统计
        supplies_res = admin_client.get_supplies_pending(1, 1)

        # 帖子统计
        messages_res = admin_client.get_messages_pending(1, 1)

        return Response({
            'activities': {
                'pending': activities_res.get('count', 0) or 0,
                'approved': 0,
                'rejected': 0,
            },
            'communities': {
                'pending': communities_res.get('count', 0) or 0,
            },
            'supplies': {
                'pending': supplies_res.get('count', 0) or 0,
            },
            'messages': {
                'pending': messages_res.get('count', 0) or 0,
            },
        })