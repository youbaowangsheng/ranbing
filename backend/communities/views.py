"""Communities视图"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Community, CommunityMember, Message
from .serializers import CommunitySerializer, MessageSerializer
from profiles.models import Profile


class CommunityViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Community.objects.select_related('owner__user').filter(
            status__in=[1, 2]
        )

    def list(self, request):
        qs = self.get_queryset()
        comm_type = request.query_params.get('type')
        school = request.query_params.get('school', '')

        if comm_type:
            qs = qs.filter(community_type=int(comm_type))
        if school:
            qs = qs.filter(school__icontains=school)

        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(CommunitySerializer(page, many=True).data)
        return Response({'code': 0, 'data': CommunitySerializer(qs, many=True).data})

    def retrieve(self, request, pk=None):
        try:
            community = self.get_queryset().get(uuid=pk)
        except Community.DoesNotExist:
            return Response({'code': 2001, 'message': '社群不存在'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'code': 0, 'data': CommunitySerializer(community).data})

    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        try:
            community = Community.objects.get(uuid=pk)
        except Community.DoesNotExist:
            return Response({'code': 2001, 'message': '社群不存在'}, status=status.HTTP_404_NOT_FOUND)

        profile, _ = Profile.objects.get_or_create(user=request.user)
        member, created = CommunityMember.objects.get_or_create(
            community=community, profile=profile, defaults={'role': 1, 'status': 1}
        )
        if not created:
            if member.status == 1:
                return Response({'code': 2003, 'message': '您已在社群中'}, status=status.HTTP_400_BAD_REQUEST)
            member.status = 1
            member.save()

        community.member_count += 1
        community.save(update_fields=['member_count'])
        return Response({'code': 0, 'message': '加入成功'}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        try:
            community = Community.objects.get(uuid=pk)
        except Community.DoesNotExist:
            return Response({'code': 2001, 'message': '社群不存在'}, status=status.HTTP_404_NOT_FOUND)

        profile, _ = Profile.objects.get_or_create(user=request.user)
        try:
            member = CommunityMember.objects.get(community=community, profile=profile, status=1)
        except CommunityMember.DoesNotExist:
            return Response({'code': 2004, 'message': '您不在社群中'}, status=status.HTTP_400_BAD_REQUEST)

        member.status = 2  # 已退出
        member.save(update_fields=['status'])
        community.member_count = max(0, community.member_count - 1)
        community.save(update_fields=['member_count'])
        return Response({'code': 0, 'message': '已退出社群'})

    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        try:
            community = Community.objects.get(uuid=pk)
        except Community.DoesNotExist:
            return Response({'code': 2001, 'message': '社群不存在'}, status=status.HTTP_404_NOT_FOUND)

        qs = Message.objects.filter(community=community).select_related('profile__user')
        signal_type = request.query_params.get('signal_type')
        if signal_type:
            qs = qs.filter(ai_signal_type=int(signal_type))

        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(MessageSerializer(page, many=True).data)
        return Response({'code': 0, 'data': MessageSerializer(qs[:20], many=True).data})

    @action(detail=False, methods=['get'])
    def pending(self, request):
        """待审核社群列表"""
        qs = self.get_queryset().filter(audit_status=0)
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(CommunitySerializer(page, many=True).data)
        return Response({'code': 0, 'data': CommunitySerializer(qs, many=True).data})

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """审核通过"""
        try:
            community = Community.objects.get(uuid=pk)
        except Community.DoesNotExist:
            return Response({'code': 2001, 'message': '社群不存在'}, status=status.HTTP_404_NOT_FOUND)
        community.audit_status = 1
        community.save(update_fields=['audit_status'])
        return Response({'code': 0, 'message': '审核通过'})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """审核拒绝"""
        try:
            community = Community.objects.get(uuid=pk)
        except Community.DoesNotExist:
            return Response({'code': 2001, 'message': '社群不存在'}, status=status.HTTP_404_NOT_FOUND)
        community.audit_status = 2
        community.save(update_fields=['audit_status'])
        return Response({'code': 0, 'message': '审核拒绝'})

    @action(detail=False, methods=['get'])
    def pending_messages(self, request):
        """待审核消息列表"""
        qs = Message.objects.filter(audit_status=0).select_related('profile__user', 'community')
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(MessageSerializer(page, many=True).data)
        return Response({'code': 0, 'data': MessageSerializer(qs[:20], many=True).data})

    @action(detail=True, methods=['post'], url_path='messages/(?P<msg_id>[^/.]+)/audit')
    def audit_message(self, request, pk=None, msg_id=None):
        """审核消息"""
        try:
            msg = Message.objects.get(id=msg_id, community=pk)
        except Message.DoesNotExist:
            return Response({'code': 2002, 'message': '消息不存在'}, status=status.HTTP_404_NOT_FOUND)

        action = request.data.get('action')  # 'approve' or 'reject'
        if action == 'approve':
            msg.audit_status = 1
        else:
            msg.audit_status = 2
        msg.save(update_fields=['audit_status'])
        return Response({'code': 0, 'message': '审核完成'})

    @action(detail=False, methods=['post'])
    def post_message(self, request):
        community_uuid = request.data.get('community_uuid')
        content = request.data.get('content', '')

        try:
            community = Community.objects.get(uuid=community_uuid)
        except Community.DoesNotExist:
            return Response({'code': 2001, 'message': '社群不存在'}, status=status.HTTP_404_NOT_FOUND)

        profile, _ = Profile.objects.get_or_create(user=request.user)
        msg = Message.objects.create(
            community=community, profile=profile, content=content, msg_type=1
        )

        # TODO: AI信号识别
        return Response({
            'code': 0,
            'data': {
                'uuid': str(msg.uuid),
                'message': '发布成功'
            }
        }, status=status.HTTP_201_CREATED)
