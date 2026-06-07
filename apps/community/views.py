from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.core.models import CommunityPost
from .serializers import CommunityPostSerializer
from apps.admin_client import get_admin_client


class CommunityPostViewSet(viewsets.ModelViewSet):
    """社群内容管理 API - 调用 backend 审核"""
    serializer_class = CommunityPostSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return CommunityPost.objects.none()
        return CommunityPost.objects.filter(user=user)

    def list(self, request):
        """获取帖子列表（从 backend）"""
        admin_client = get_admin_client()
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))

        # 获取待审核消息（从 backend）
        result = admin_client.get_messages_pending(page, page_size)
        return Response(result)

    @action(detail=False, methods=['get'])
    def pending(self, request):
        """待审核帖子"""
        admin_client = get_admin_client()
        result = admin_client.get_messages_pending()
        return Response(result)

    @action(detail=True, methods=['post'], url_path='approve')
    def approve_post(self, request, pk=None):
        """审核通过帖子"""
        admin_client = get_admin_client()
        # pk = community_uuid:msg_id
        parts = str(pk).split(':')
        if len(parts) == 2:
            community_uuid, msg_id = parts
            result = admin_client.audit_message(community_uuid, int(msg_id), 'approve')
            return Response(result)
        return Response({'code': 400, 'message': '无效的帖子ID'})

    @action(detail=True, methods=['post'], url_path='reject')
    def reject_post(self, request, pk=None):
        """审核拒绝帖子"""
        admin_client = get_admin_client()
        comment = request.data.get('comment', '')
        parts = str(pk).split(':')
        if len(parts) == 2:
            community_uuid, msg_id = parts
            result = admin_client.audit_message(community_uuid, int(msg_id), 'reject')
            return Response(result)
        return Response({'code': 400, 'message': '无效的帖子ID'})