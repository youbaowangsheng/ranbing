"""Communities视图"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from django.utils import timezone

from .models import Community, CommunityMember, Message
from .serializers import CommunitySerializer, MessageSerializer
from profiles.models import Profile


class CommunityViewSet(viewsets.GenericViewSet):
    # 列表/详情/消息/成员公开；加入/退出/发帖需登录；审核接口需 staff
    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'messages', 'members']:
            return [AllowAny()]
        if self.action in ['pending', 'approve', 'reject', 'pending_messages', 'audit_message']:
            return [IsAdminUser()]
        return [IsAuthenticated()]

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

        member.status = 2  # 已退出（STATUS_CHOICES: 2=已退出）
        member.save(update_fields=['status'])
        community.member_count = max(0, community.member_count - 1)
        community.save(update_fields=['member_count'])
        return Response({'code': 0, 'message': '已退出社群'})

    @action(detail=False, methods=['post'], url_path='post_message')
    def post_message(self, request):
        """POST /api/v1/communities/post_message/ — 发布社群消息
        前端入参: { community_uuid, content }
        """
        community_uuid = request.data.get('community_uuid')
        content = (request.data.get('content') or '').strip()

        if not community_uuid:
            return Response({'code': 4001, 'message': '缺少 community_uuid'}, status=status.HTTP_400_BAD_REQUEST)
        if not content:
            return Response({'code': 4002, 'message': '内容不能为空'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            community = Community.objects.get(uuid=community_uuid)
        except Community.DoesNotExist:
            return Response({'code': 2001, 'message': '社群不存在'}, status=status.HTTP_404_NOT_FOUND)

        profile, _ = Profile.objects.get_or_create(
            user=request.user,
            defaults={'real_name': request.user.nickname or '未命名'}
        )
        is_member = CommunityMember.objects.filter(
            community=community, profile=profile
        ).exists()
        if not is_member:
            return Response({'code': 1002, 'message': '请先加入社群再发帖'}, status=status.HTTP_403_FORBIDDEN)

        message = Message.objects.create(
            community=community,
            profile=profile,
            content=content,
            audit_status=0,
        )
        return Response({
            'code': 0,
            'message': '发布成功，待审核',
            'data': {'id': message.id}
        })

    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        """GET /api/v1/communities/{uuid}/members/ — 社群成员列表"""
        try:
            community = Community.objects.get(uuid=pk)
        except Community.DoesNotExist:
            return Response({'code': 2001, 'message': '社群不存在'}, status=status.HTTP_404_NOT_FOUND)

        qs = CommunityMember.objects.filter(community=community, status=1).select_related(
            'profile__user'
        )
        page = self.paginate_queryset(qs)

        def _ser(m):
            p = m.profile
            return {
                'profile': {
                    'uuid': str(p.uuid) if p else '',
                    'real_name': p.real_name if p else '匿名',
                    'company': p.company if p else '',
                    'position': p.position if p else '',
                    'avatar_url': getattr(p.user, 'avatar_url', '') if p and p.user else '',
                },
                'role': m.role,
                'joined_at': m.joined_at.isoformat() if m.joined_at else None,
            }

        if page is not None:
            return self.get_paginated_response([_ser(m) for m in page])
        return Response({'code': 0, 'data': [_ser(m) for m in qs[:20]]})

    @action(detail=True, methods=['get'], url_path='my_status')
    def my_status(self, request, pk=None):
        """当前用户在该社群的状态（是否已加入、角色）"""
        try:
            community = Community.objects.get(uuid=pk)
        except Community.DoesNotExist:
            return Response({'code': 2001, 'message': '社群不存在'}, status=status.HTTP_404_NOT_FOUND)

        if not request.user.is_authenticated:
            return Response({'code': 0, 'data': {'joined': False, 'role': None}})

        profile, _ = Profile.objects.get_or_create(user=request.user)
        member = CommunityMember.objects.filter(
            community=community, profile=profile, status=1
        ).first()
        return Response({'code': 0, 'data': {
            'joined': bool(member),
            'role': member.role if member else None,
        }})

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
        community.audit_time = timezone.now()
        community.save(update_fields=['audit_status', 'audit_time'])
        return Response({'code': 0, 'message': '审核通过'})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """审核拒绝"""
        try:
            community = Community.objects.get(uuid=pk)
        except Community.DoesNotExist:
            return Response({'code': 2001, 'message': '社群不存在'}, status=status.HTTP_404_NOT_FOUND)
        community.audit_status = 2
        community.audit_time = timezone.now()
        community.save(update_fields=['audit_status', 'audit_time'])
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
            community = Community.objects.get(uuid=pk)
        except Community.DoesNotExist:
            return Response({'code': 2001, 'message': '社群不存在'}, status=status.HTTP_404_NOT_FOUND)
        try:
            msg = Message.objects.get(id=msg_id, community=community)
        except Message.DoesNotExist:
            return Response({'code': 2002, 'message': '消息不存在'}, status=status.HTTP_404_NOT_FOUND)

        action = request.data.get('action')  # 'approve' or 'reject'
        if action == 'approve':
            msg.audit_status = 1
        else:
            msg.audit_status = 2
        msg.save(update_fields=['audit_status'])
        return Response({'code': 0, 'message': '审核完成'})

    # 注意：post_message 已在上方定义（含成员校验 + 审核），此处不再重复定义
