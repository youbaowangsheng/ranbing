"""Supplies视图"""
import math
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q

from .models import Supply, Match, Connection, Followup, FriendRequest, Card
from .serializers import (
    SupplyListSerializer, SupplyDetailSerializer, SupplyCreateSerializer,
    SupplyFeedSerializer, MatchSerializer, ConnectionSerializer, FollowupSerializer,
    FriendRequestSerializer, CardSerializer, CardDetailSerializer
)
from profiles.models import Profile


def _cosine_similarity(vec_a, vec_b):
    """计算两个向量的余弦相似度"""
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class SupplyViewSet(viewsets.GenericViewSet):
    """供需相关API"""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Supply.objects.select_related('profile__user').filter(
            audit_status=1, status=1
        )

    def get_serializer_class(self):
        return {
            'list': SupplyListSerializer,
            'retrieve': SupplyDetailSerializer,
            'create': SupplyCreateSerializer,
            'feed': SupplyFeedSerializer,
        }.get(self.action, SupplyDetailSerializer)

    def list(self, request):
        qs = self.get_queryset()
        supply_type = request.query_params.get('type')
        tag_ids = request.query_params.get('tag_ids', '')
        keyword = request.query_params.get('keyword', '')

        if supply_type:
            qs = qs.filter(supply_type=int(supply_type))
        if tag_ids:
            tag_list = [int(x) for x in tag_ids.split(',')]
            # JSONField contains list: check if any tag_id is in the JSON array
            from django.db.models import Q
            tag_q = Q()
            for tid in tag_list:
                tag_q |= Q(tags__contains=[tid])
            qs = qs.filter(tag_q)
        if keyword:
            qs = qs.filter(Q(title__icontains=keyword) | Q(content__icontains=keyword))

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = SupplyListSerializer(page, many=True, context={'request': request, 'profile': request.user.profile})
            return self.get_paginated_response(serializer.data)

        serializer = SupplyListSerializer(qs, many=True)
        return Response({'code': 0, 'data': serializer.data})

    def retrieve(self, request, pk=None):
        try:
            supply = Supply.objects.select_related('profile__user').get(uuid=pk)
        except Supply.DoesNotExist:
            return Response({'code': 2001, 'message': '供需不存在'}, status=status.HTTP_404_NOT_FOUND)
        supply.view_count += 1
        supply.save(update_fields=['view_count'])
        serializer = SupplyDetailSerializer(supply)
        return Response({'code': 0, 'data': serializer.data})

    def create(self, request):
        serializer = SupplyCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile, _ = Profile.objects.get_or_create(user=request.user)
        from datetime import timedelta
        from django.utils import timezone
        supply = Supply.objects.create(
            profile=profile,
            **serializer.validated_data,
            expires_at=timezone.now() + timedelta(days=30)
        )
        # 生成embedding + AI质量评分（同步，简单实现）
        try:
            from ai.services.deepseek import DeepSeekClient
            client = DeepSeekClient()
            combined_text = f"{supply.title} {supply.content}"
            emb = client.embedding(combined_text)
            if emb and len(emb) > 10:
                from supplies.models import SupplyEmbedding
                SupplyEmbedding.objects.update_or_create(
                    supply=supply,
                    defaults={'embedding': emb, 'model_name': 'text-embedding-3-small'}
                )
                supply.quality_score = min(len(emb) / 1536 * 0.3 + 0.5, 0.99)
                supply.save(update_fields=['quality_score'])
        except Exception as e:
            print(f'[Feed Embedding Error] {e}')
        return Response({'code': 0, 'data': {'uuid': str(supply.uuid), 'quality_score': supply.quality_score}},
                       status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def pending(self, request):
        """待审核供需列表"""
        qs = Supply.objects.select_related('profile__user').filter(audit_status=0)
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(SupplyListSerializer(page, many=True).data)
        return Response({'code': 0, 'data': SupplyListSerializer(qs, many=True).data})

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """审核通过"""
        try:
            supply = Supply.objects.get(uuid=pk)
        except Supply.DoesNotExist:
            return Response({'code': 2001, 'message': '供需不存在'}, status=status.HTTP_404_NOT_FOUND)
        supply.audit_status = 1
        supply.save(update_fields=['audit_status'])
        return Response({'code': 0, 'message': '审核通过'})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """审核拒绝"""
        try:
            supply = Supply.objects.get(uuid=pk)
        except Supply.DoesNotExist:
            return Response({'code': 2001, 'message': '供需不存在'}, status=status.HTTP_404_NOT_FOUND)
        supply.audit_status = 2
        supply.save(update_fields=['audit_status'])
        return Response({'code': 0, 'message': '审核拒绝'})

    @action(detail=False, methods=['get'])
    def feed(self, request):
        """AI推荐Feed — 基于embedding的语义相似度"""
        from ai.services.deepseek import DeepSeekClient

        profile, _ = Profile.objects.get_or_create(user=request.user)
        client = DeepSeekClient()

        # 获取用户profile的embedding
        user_emb = None
        try:
            from profiles.models import ProfileEmbedding
            pe = ProfileEmbedding.objects.get(profile=profile)
            user_emb = pe.embedding
        except ProfileEmbedding.DoesNotExist:
            pass

        # 如果没有embedding，用用户标签构造一个描述文本
        user_tag_ids = list(profile.profile_tags.values_list('tag_id', flat=True))
        user_tag_names = list(profile.profile_tags.values_list('tag__name', flat=True))
        user_text = ' '.join(user_tag_names) if user_tag_names else '创业 投资 企业服务'
        if not user_emb:
            user_emb = client.embedding(user_text)
            # 缓存到profile
            try:
                from profiles.models import ProfileEmbedding
                ProfileEmbedding.objects.update_or_create(
                    profile=profile,
                    defaults={'embedding': user_emb, 'model_name': 'text-embedding-3-small'}
                )
            except Exception:
                pass

        if not user_emb or len(user_emb) < 10:
            # fallback: 纯标签匹配
            user_tag_ids = list(profile.profile_tags.values_list('tag_id', flat=True))
            if not user_tag_ids:
                return Response({'code': 0, 'data': {'items': []}})
            qs = Supply.objects.filter(status=1).exclude(profile=profile).filter(
                tags__overlap=user_tag_ids
            ).select_related('profile__user').order_by('-created_at')[:20]
            items = []
            for s in qs:
                overlap = set(s.tags) & set(user_tag_ids)
                score = min(len(overlap) * 0.2 + 0.5, 0.99)
                items.append({
                    'uuid': str(s.uuid),
                    'profile': {
                        'uuid': str(s.profile.uuid),
                        'real_name': s.profile.real_name,
                        'company': s.profile.company,
                        'position': s.profile.position,
                        'cert_level': s.profile.cert_level,
                        'avatar_url': s.profile.user.avatar_url,
                    },
                    'supply_type': s.supply_type,
                    'title': s.title,
                    'tags': [{'id': t} for t in s.tags],
                    'match_score': round(score, 4),
                    'match_reason': f'与您的{len(overlap)}个标签匹配',
                    'created_at': s.created_at,
                })
            return Response({'code': 0, 'data': {'items': items}})

        # 获取有embedding的供给，计算相似度
        from supplies.models import SupplyEmbedding
        candidates = list(SupplyEmbedding.objects.select_related('supply').exclude(
            supply__profile=profile
        ).filter(supply__status=1)[:100])

        scored = []
        for se in candidates:
            if not se.embedding or len(se.embedding) < 10:
                continue
            sim = _cosine_similarity(user_emb, se.embedding)
            scored.append((sim, se.supply))

        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[:20]

        items = []
        for sim, supply in top:
            overlap_tags = set(supply.tags) & set(user_tag_ids) if user_tag_ids else set()
            reason = f'语义匹配度{int(sim*100)}%'
            if overlap_tags:
                reason += f' + {len(overlap_tags)}个标签'
            items.append({
                'uuid': str(supply.uuid),
                'profile': {
                    'uuid': str(supply.profile.uuid),
                    'real_name': supply.profile.real_name,
                    'company': supply.profile.company,
                    'position': supply.profile.position,
                    'cert_level': supply.profile.cert_level,
                    'avatar_url': supply.profile.user.avatar_url,
                },
                'supply_type': supply.supply_type,
                'title': supply.title,
                'tags': [{'id': t} for t in supply.tags],
                'match_score': round(sim, 4),
                'match_reason': reason,
                'created_at': supply.created_at,
            })

        return Response({'code': 0, 'data': {'items': items}})

    @action(detail=False, methods=['get', 'post'], url_path='connections')
    def connections_list(self, request):
        """我的关系链"""
        if request.method == 'GET':
            qs = Connection.objects.filter(
                Q(user_a=request.user) | Q(user_b=request.user),
                status=1
            ).select_related('user_b__profile', 'user_a__profile')
            serializer = ConnectionSerializer(qs, many=True)
            return Response({'code': 0, 'data': serializer.data})
        # POST: 建立连接
        target_uuid = request.data.get('target_profile_uuid')
        try:
            target_profile = Profile.objects.get(uuid=target_uuid)
        except Profile.DoesNotExist:
            return Response({'code': 2001, 'message': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)
        conn = Connection.objects.create(
            user_a=request.user, user_b=target_profile.user,
            conn_type=5
        )
        return Response({'code': 0, 'data': {'uuid': str(conn.uuid)}}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get', 'put'])
    def followups(self, request):
        """AI跟进列表"""
        if request.method == 'GET':
            profile, _ = Profile.objects.get_or_create(user=request.user)
            qs = Followup.objects.filter(from_profile=profile).order_by('-scheduled_at')
            page = self.paginate_queryset(qs)
            if page is not None:
                serializer = FollowupSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            serializer = FollowupSerializer(qs, many=True)
            return Response({'code': 0, 'data': serializer.data})

        # PUT: 更新跟进状态
        followup_uuid = request.data.get('uuid')
        try:
            fu = Followup.objects.get(uuid=followup_uuid, from_profile__user=request.user)
        except Followup.DoesNotExist:
            return Response({'code': 2001, 'message': '跟进记录不存在'}, status=status.HTTP_404_NOT_FOUND)
        if 'status' in request.data:
            fu.status = request.data['status']
        if 'result' in request.data:
            fu.result = request.data['result']
        fu.save()
        return Response({'code': 0, 'message': '更新成功'})

    @action(detail=False, methods=['get'])
    def mine(self, request):
        """当前用户发布的所有供需（所有状态）"""
        profile, _ = Profile.objects.get_or_create(user=request.user)
        qs = Supply.objects.filter(profile=profile).order_by('-created_at')
        serializer = SupplyListSerializer(qs, many=True)
        return Response({'code': 0, 'data': serializer.data})


class FriendRequestViewSet(viewsets.GenericViewSet):
    """好友请求相关API"""
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return FriendRequestSerializer
        return FriendRequestSerializer

    def get_queryset(self):
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        return FriendRequest.objects.filter(to_profile=profile).select_related('from_profile__user')

    def list(self, request):
        """我收到的加好友请求列表"""
        qs = self.get_queryset().filter(status=1).order_by('-created_at')
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = FriendRequestSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = FriendRequestSerializer(qs, many=True)
        return Response({'code': 0, 'data': serializer.data})

    @action(detail=False, methods=['get'])
    def sent(self, request):
        """我发出去的好友请求列表"""
        profile, _ = Profile.objects.get_or_create(user=request.user)
        qs = FriendRequest.objects.filter(from_profile=profile).select_related('to_profile__user').order_by('-created_at')
        serializer = FriendRequestSerializer(qs, many=True)
        return Response({'code': 0, 'data': serializer.data})

    @action(detail=False, methods=['post'])
    def send(self, request):
        """发送好友请求"""
        target_uuid = request.data.get('target_uuid')
        message = request.data.get('message', '').strip()
        if not target_uuid:
            return Response({'code': 4001, 'message': '缺少target_uuid'})

        try:
            target = Profile.objects.get(uuid=target_uuid)
        except Profile.DoesNotExist:
            return Response({'code': 2001, 'message': '用户不存在'})

        if target.user == request.user:
            return Response({'code': 4002, 'message': '不能给自己发请求'})

        # 检查是否已经是好友
        if Connection.objects.filter(
            Q(user_a=request.user, user_b=target.user) |
            Q(user_a=target.user, user_b=request.user),
            status=1
        ).exists():
            return Response({'code': 0, 'message': '你们已经是好友了'})

        profile, _ = Profile.objects.get_or_create(user=request.user)
        # 检查是否已有待处理请求
        existing = FriendRequest.objects.filter(
            from_profile=profile, to_profile=target, status=1
        ).first()
        if existing:
            return Response({'code': 0, 'message': '已发送过请求，等待对方接受', 'data': {'uuid': str(existing.uuid)}})

        fr = FriendRequest.objects.create(
            from_profile=profile,
            to_profile=target,
            message=message,
            status=1
        )
        return Response({
            'code': 0,
            'message': '请求已发送',
            'data': {'uuid': str(fr.uuid)}
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def accept(self, request):
        """接受好友请求"""
        req_uuid = request.data.get('uuid')
        if not req_uuid:
            return Response({'code': 4001, 'message': '缺少uuid'})

        profile, _ = Profile.objects.get_or_create(user=request.user)
        try:
            fr = FriendRequest.objects.get(uuid=req_uuid, to_profile=profile, status=1)
        except FriendRequest.DoesNotExist:
            return Response({'code': 4041, 'message': '请求不存在或已处理'})

        # 建立双向好友关系（保证 user_a < user_b）
        user_a, user_b = fr.from_profile.user_id, fr.to_profile.user_id
        Connection.objects.get_or_create(
            user_a_id=min(user_a, user_b),
            user_b_id=max(user_a, user_b),
            defaults={'conn_type': 1, 'status': 1}
        )
        fr.status = 2
        fr.save()

        # 更新双方的 conn_count
        for prof in [fr.from_profile, fr.to_profile]:
            prof.conn_count = Connection.objects.filter(
                Q(user_a=prof.user, status=1) | Q(user_b=prof.user, status=1)
            ).count()
            prof.save(update_fields=['conn_count'])

        return Response({'code': 0, 'message': '已接受，你们现在是好友了'})

    @action(detail=False, methods=['post'])
    def reject(self, request):
        """拒绝好友请求"""
        req_uuid = request.data.get('uuid')
        if not req_uuid:
            return Response({'code': 4001, 'message': '缺少uuid'})

        profile, _ = Profile.objects.get_or_create(user=request.user)
        try:
            fr = FriendRequest.objects.get(uuid=req_uuid, to_profile=profile, status=1)
        except FriendRequest.DoesNotExist:
            return Response({'code': 4041, 'message': '请求不存在或已处理'})

        fr.status = 3
        fr.save()
        return Response({'code': 0, 'message': '已拒绝'})


class ConnectionViewSet(viewsets.GenericViewSet):
    """关系链相关API"""
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return ConnectionSerializer
        return ConnectionSerializer

    def get_queryset(self):
        return Connection.objects.filter(
            Q(user_a=self.request.user) | Q(user_b=self.request.user),
            status=1
        ).select_related('user_a__profile', 'user_b__profile')

    def list(self, request):
        """我的关系链列表"""
        qs = self.get_queryset().order_by('-relation_strength', '-created_at')
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = ConnectionSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = ConnectionSerializer(qs, many=True)
        return Response({'code': 0, 'data': serializer.data})

    def retrieve(self, request, pk=None):
        """关系链详情"""
        try:
            conn = Connection.objects.get(uuid=pk, status=1)
        except Connection.DoesNotExist:
            return Response({'code': 2001, 'message': '关系链不存在'}, status=status.HTTP_404_NOT_FOUND)
        serializer = ConnectionSerializer(conn)
        return Response({'code': 0, 'data': serializer.data})

    @action(detail=False, methods=['post'])
    def connect(self, request):
        """建立关系链（直接加好友，不需要请求）"""
        target_uuid = request.data.get('target_profile_uuid')
        conn_type = request.data.get('conn_type', 1)
        if not target_uuid:
            return Response({'code': 4001, 'message': '缺少target_profile_uuid'})

        try:
            target_profile = Profile.objects.get(uuid=target_uuid)
        except Profile.DoesNotExist:
            return Response({'code': 2001, 'message': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)

        if target_profile.user == request.user:
            return Response({'code': 4002, 'message': '不能与自己建立关系'})

        # 检查是否已存在
        existing = Connection.objects.filter(
            Q(user_a=request.user, user_b=target_profile.user) |
            Q(user_a=target_profile.user, user_b=request.user),
            status=1
        ).first()
        if existing:
            return Response({'code': 0, 'message': '你们已经是好友了', 'data': {'uuid': str(existing.uuid)}})

        conn = Connection.objects.create(
            user_a=request.user,
            user_b=target_profile.user,
            conn_type=conn_type
        )
        return Response({'code': 0, 'data': {'uuid': str(conn.uuid)}}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def delete(self, request, pk=None):
        """删除关系链"""
        try:
            conn = Connection.objects.get(uuid=pk, status=1)
        except Connection.DoesNotExist:
            return Response({'code': 2001, 'message': '关系链不存在'}, status=status.HTTP_404_NOT_FOUND)

        # 只允许关系统中的当事人删除
        if request.user not in [conn.user_a, conn.user_b]:
            return Response({'code': 1002, 'message': '无权限'}, status=status.HTTP_403_FORBIDDEN)

        conn.status = 2
        conn.save()
        return Response({'code': 0, 'message': '已删除'})

    @action(detail=False, methods=['get'])
    def count(self, request):
        """关系链数量统计"""
        profile, _ = Profile.objects.get_or_create(user=request.user)
        total = Connection.objects.filter(
            Q(user_a=request.user) | Q(user_b=request.user),
            status=1
        ).count()
        return Response({'code': 0, 'data': {'total': total, 'conn_count': profile.conn_count}})


class CardViewSet(viewsets.GenericViewSet):
    """电子名片相关API"""
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ('retrieve',):
            return CardDetailSerializer
        return CardSerializer

    def get_queryset(self):
        return Card.objects.filter(status=1).select_related('owner__user')

    @action(detail=False, methods=['get', 'put', 'post'])
    def me(self, request):
        """获取/创建/更新我的名片"""
        profile, _ = Profile.objects.get_or_create(user=request.user)
        card, created = Card.objects.get_or_create(owner=profile)

        if request.method == 'GET':
            return Response({'code': 0, 'data': CardDetailSerializer(card).data})

        serializer = CardSerializer(card, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'code': 0, 'message': '更新成功'})

    def retrieve(self, request, pk=None):
        """查看他人名片（通过uuid）"""
        try:
            card = Card.objects.get(uuid=pk, status=1)
        except Card.DoesNotExist:
            return Response({'code': 2001, 'message': '名片不存在'}, status=status.HTTP_404_NOT_FOUND)

        # 增加浏览次数
        card.view_count += 1
        card.save(update_fields=['view_count'])

        return Response({'code': 0, 'data': CardDetailSerializer(card).data})

    @action(detail=True, methods=['get'])
    def by_profile(self, request, pk=None):
        """通过profile_uuid获取名片"""
        try:
            profile = Profile.objects.get(uuid=pk)
            card = Card.objects.get(owner=profile, status=1)
        except (Profile.DoesNotExist, Card.DoesNotExist):
            return Response({'code': 2001, 'message': '名片不存在'}, status=status.HTTP_404_NOT_FOUND)

        card.view_count += 1
        card.save(update_fields=['view_count'])

        return Response({'code': 0, 'data': CardDetailSerializer(card).data})
