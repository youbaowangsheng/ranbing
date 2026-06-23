"""Console管理后台API"""
from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum, Count, Max
from django.contrib.auth.models import User
from django.conf import settings
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from .models import AgentConfig, UsageRecord, MatchingRecord, PublishTask
from .serializers import (
    AgentConfigSerializer, AgentConfigCreateSerializer,
    UsageRecordSerializer, MatchingRecordSerializer, PublishTaskSerializer
)


class DashboardStatsView(APIView):
    """Dashboard统计"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()
        month_start = today.replace(day=1)

        users_total = User.objects.count()
        agents_total = AgentConfig.objects.count()
        matching_total = MatchingRecord.objects.count()
        publish_total = PublishTask.objects.count()

        return Response({
            'code': 0,
            'data': {
                'users_total': users_total,
                'agents_total': agents_total,
                'matching_total': matching_total,
                'publish_total': publish_total,
            }
        })


class DailyStatsView(APIView):
    """每日用量统计"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        days = int(request.query_params.get('days', 7))
        start_date = timezone.now() - timedelta(days=days)

        records = UsageRecord.objects.filter(
            created_at__gte=start_date
        ).extra(
            select={'date': 'date(created_at)'}
        ).values('date').annotate(
            tokens=Sum('tokens'),
            cost=Sum('cost'),
            requests=Sum('request_count'),
        ).order_by('date')

        return Response({
            'code': 0,
            'data': [{
                'date': r['date'],
                'tokens': r['tokens'] or 0,
                'cost': float(r['cost'] or 0),
                'requests': r['requests'] or 0,
            } for r in records]
        })


class UsageReportView(APIView):
    """用量报表"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        days = int(request.query_params.get('days', 30))
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        start_date = timezone.now() - timedelta(days=days)

        records = UsageRecord.objects.filter(
            created_at__gte=start_date
        ).select_related('user', 'agent').order_by('-created_at')

        total = records.count()
        start = (page - 1) * page_size
        end = start + page_size
        page_records = records[start:end]

        return Response({
            'code': 0,
            'data': UsageRecordSerializer(page_records, many=True).data,
            'total': total,
            'page': page,
            'page_size': page_size,
        })


class AgentsRankView(APIView):
    """Agent排行"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        agents = AgentConfig.objects.annotate(
            total_tokens=Sum('usage_records__tokens'),
            total_cost=Sum('usage_records__cost'),
            total_requests=Sum('usage_records__request_count'),
        ).order_by('-total_tokens')[:20]

        data = [{
            'id': a.id,
            'agent_name': a.agent_name,
            'agent_type': a.agent_type,
            'user': a.user.username,
            'total_tokens': a.total_tokens or 0,
            'total_cost': float(a.total_cost or 0),
            'total_requests': a.total_requests or 0,
        } for a in agents]

        return Response({'code': 0, 'data': data})


class BusinessAgentViewSet(viewsets.GenericViewSet):
    """业务Agent管理"""
    permission_classes = [IsAuthenticated]
    serializer_class = AgentConfigSerializer

    def get_queryset(self):
        return AgentConfig.objects.select_related('user').order_by('-created_at')

    def list(self, request):
        qs = self.get_queryset()
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(AgentConfigSerializer(page, many=True).data)
        return Response({'code': 0, 'data': AgentConfigSerializer(qs, many=True).data})

    def retrieve(self, request, pk=None):
        try:
            agent = AgentConfig.objects.get(pk=pk)
        except AgentConfig.DoesNotExist:
            return Response({'code': 4041, 'message': 'Agent不存在'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'code': 0, 'data': AgentConfigSerializer(agent).data})

    def create(self, request):
        serializer = AgentConfigCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        agent = AgentConfig.objects.create(**serializer.validated_data)
        return Response({'code': 0, 'data': AgentConfigSerializer(agent).data}, status=status.HTTP_201_CREATED)

    def partial_update(self, request, pk=None):
        try:
            agent = AgentConfig.objects.get(pk=pk)
        except AgentConfig.DoesNotExist:
            return Response({'code': 4041, 'message': 'Agent不存在'}, status=status.HTTP_404_NOT_FOUND)
        serializer = AgentConfigCreateSerializer(agent, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'code': 0, 'data': AgentConfigSerializer(agent).data})

    def destroy(self, request, pk=None):
        try:
            agent = AgentConfig.objects.get(pk=pk)
        except AgentConfig.DoesNotExist:
            return Response({'code': 4041, 'message': 'Agent不存在'}, status=status.HTTP_404_NOT_FOUND)
        agent.delete()
        return Response({'code': 0, 'message': '删除成功'})

    @action(detail=False, methods=['get'])
    def types(self, request):
        return Response({'code': 0, 'data': AgentConfig.AGENT_TYPE_CHOICES})

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        try:
            agent = AgentConfig.objects.get(pk=pk)
        except AgentConfig.DoesNotExist:
            return Response({'code': 4041, 'message': 'Agent不存在'}, status=status.HTTP_404_NOT_FOUND)

        records = agent.usage_records.all()
        total_tokens = records.aggregate(t=Sum('tokens'))['t'] or 0
        total_cost = records.aggregate(c=Sum('cost'))['c'] or 0
        total_requests = records.aggregate(r=Sum('request_count'))['r'] or 0

        return Response({
            'code': 0,
            'data': {
                'total_tokens': total_tokens,
                'total_cost': float(total_cost),
                'total_requests': total_requests,
            }
        })


class MatchingRecordViewSet(viewsets.GenericViewSet):
    """匹配记录"""
    permission_classes = [IsAuthenticated]
    serializer_class = MatchingRecordSerializer

    def get_queryset(self):
        return MatchingRecord.objects.select_related('user', 'agent').order_by('-created_at')

    def list(self, request):
        qs = self.get_queryset()
        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(MatchingRecordSerializer(page, many=True).data)
        return Response({'code': 0, 'data': MatchingRecordSerializer(qs, many=True).data})

    def partial_update(self, request, pk=None):
        try:
            record = MatchingRecord.objects.get(pk=pk)
        except MatchingRecord.DoesNotExist:
            return Response({'code': 4041, 'message': '记录不存在'}, status=status.HTTP_404_NOT_FOUND)
        if 'status' in request.data:
            record.status = request.data['status']
        record.save()
        return Response({'code': 0, 'data': MatchingRecordSerializer(record).data})


class PublishTaskViewSet(viewsets.GenericViewSet):
    """发布任务"""
    permission_classes = [IsAuthenticated]
    serializer_class = PublishTaskSerializer

    def get_queryset(self):
        return PublishTask.objects.select_related('user', 'agent').order_by('-created_at')

    def list(self, request):
        qs = self.get_queryset()
        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(PublishTaskSerializer(page, many=True).data)
        return Response({'code': 0, 'data': PublishTaskSerializer(qs, many=True).data})

    def partial_update(self, request, pk=None):
        try:
            task = PublishTask.objects.get(pk=pk)
        except PublishTask.DoesNotExist:
            return Response({'code': 4041, 'message': '任务不存在'}, status=status.HTTP_404_NOT_FOUND)
        if 'status' in request.data:
            task.status = request.data['status']
        task.save()
        return Response({'code': 0, 'data': PublishTaskSerializer(task).data})

    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        try:
            task = PublishTask.objects.get(pk=pk)
        except PublishTask.DoesNotExist:
            return Response({'code': 4041, 'message': '任务不存在'}, status=status.HTTP_404_NOT_FOUND)
        task.status = 'pending'
        task.save(update_fields=['status'])
        return Response({'code': 0, 'message': '已重新加入队列'})
