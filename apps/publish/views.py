from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.core.models import PublishTask
from .serializers import PublishTaskSerializer
from apps.admin_client import get_admin_client


class PublishTaskViewSet(viewsets.ModelViewSet):
    """发布管理 API"""
    serializer_class = PublishTaskSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return PublishTask.objects.none()
        return PublishTask.objects.filter(user=user)

    @action(detail=False, methods=['get'])
    def pending(self, request):
        """待发布任务 - 本地 PublishTask"""
        tasks = self.get_queryset().filter(status='pending')
        return Response(PublishTaskSerializer(tasks, many=True).data)

    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        """重新提交发布任务"""
        instance = self.get_object()
        instance.status = 'pending'
        instance.save(update_fields=['status'])
        return Response({'code': 0, 'message': '已重新提交'})