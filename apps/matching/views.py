from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.core.models import MatchingRecord
from .serializers import MatchingRecordSerializer
from apps.admin_client import get_admin_client


class MatchingRecordViewSet(viewsets.ModelViewSet):
    """匹配队列 API - 调用 backend 审核"""
    serializer_class = MatchingRecordSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return MatchingRecord.objects.none()
        return MatchingRecord.objects.filter(user=user)

    def list(self, request):
        """获取匹配记录列表（本地 MatchingRecord）"""
        records = self.get_queryset().order_by('-created_at')
        return Response(MatchingRecordSerializer(records, many=True).data)

    @action(detail=False, methods=['get'])
    def pending(self, request):
        """待匹配记录"""
        records = self.get_queryset().filter(status='pending')
        return Response(MatchingRecordSerializer(records, many=True).data)

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """确认匹配"""
        instance = self.get_object()
        instance.status = 'confirmed'
        instance.save(update_fields=['status'])
        return Response({'code': 0, 'message': '已确认'})

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """取消匹配"""
        instance = self.get_object()
        instance.status = 'cancelled'
        instance.save(update_fields=['status'])
        return Response({'code': 0, 'message': '已取消'})