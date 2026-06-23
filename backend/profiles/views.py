"""Profile视图"""
import concurrent.futures

from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Profile, ProfileTag, Tag, ContactTag, ContactTagRelation
from .serializers import (
    ProfileListSerializer, ProfileDetailSerializer, ProfileEditSerializer,
    CertSubmitSerializer, ProfileTagsUpdateSerializer, TagSerializer,
    ContactTagSerializer
)

# 线程池用于CPU密集型操作（名片生成）
_card_executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)


def _generate_card_image(profile_uuid: str, profile_data: dict, tag_names: list) -> bytes:
    """
    在后台线程中生成分名片图片（CPU密集型）
    接收 profile_data dict 和 tag_names 而非 ORM 对象，避免跨线程传递 Django ORM 对象
    """
    import io
    import qrcode
    from PIL import Image, ImageDraw, ImageFont

    W, H = 600, 360

    # ── 颜色 ──
    CLR_BLUE_DARK = (26, 58, 92)
    CLR_BLUE_LIGHT = (45, 90, 140)
    CLR_ORANGE = (232, 106, 58)
    CLR_WHITE = (255, 255, 255)
    CLR_GRAY = (150, 160, 180)
    CLR_TAG_BG = (232, 240, 254)

    # ── 主图：蓝底渐变 ──
    img = Image.new('RGB', (W, H), CLR_BLUE_DARK)
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, W, H // 2], fill=CLR_BLUE_LIGHT)
    draw.ellipse([W - 160, -40, W + 40, 160], fill=(30, 70, 110))
    draw.ellipse([W - 80, 60, W + 100, 240], fill=(232, 106, 58))
    draw.rectangle([0, H - 8, W, H], fill=CLR_ORANGE)

    # ── 姓名 ──
    name = profile_data.get('real_name') or '未命名'
    for fs in range(40, 18, -2):
        try:
            fnt = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', fs)
            fnt_sm = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', fs // 2 + 6)
            fnt_xs = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', fs // 2 + 4)
            break
        except Exception:
            fnt = ImageFont.load_default()
            fnt_sm = ImageFont.load_default()
            fnt_xs = ImageFont.load_default()
            break

    bbox = draw.textbbox((0, 0), name, font=fnt)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text(((W - tw) // 2, 40), name, font=fnt, fill=CLR_WHITE)

    # 认证标签
    cert_text = ''
    if profile_data.get('cert_level') == 3:
        cert_text = '🏅 已深度认证'
    elif profile_data.get('cert_level') == 2:
        cert_text = '✓ 校友认证'
    elif profile_data.get('cert_level',0) >= 1:
        cert_text = '✓ 已认证'
    if cert_text:
        bbox2 = draw.textbbox((0, 0), cert_text, font=fnt_sm)
        cw = bbox2[2] - bbox2[0]
        draw.text(((W - cw) // 2, 40 + th + 6), cert_text, font=fnt_sm, fill=(255, 200, 150))

    # ── 公司+职位 ──
    line1 = ''
    if profile_data.get('company'):
        line1 += profile_data['company']
    if profile_data.get('position'):
        line1 += '  ·  ' + profile_data['position']
    if profile_data.get('education_school'):
        line1 += ('  |  ' if line1 else '') + profile_data['education_school']
        if profile_data.get('education_year'):
            line1 += ' ' + profile_data['education_year'] + '届'
    if not line1:
        line1 = '商务人脉'
    bbox_l1 = draw.textbbox((0, 0), line1, font=fnt_sm)
    lw = bbox_l1[2] - bbox_l1[0]
    draw.text(((W - lw) // 2, 100 + th), line1, font=fnt_sm, fill=(190, 210, 240))

    # ── 标签行 ──
    if tag_names:
        tag_y = 160 + th
        tag_pills = []
        for tname in tag_names[:6]:
            bbox_t = draw.textbbox((0, 0), tname, font=fnt_xs)
            tw_t = bbox_t[2] - bbox_t[0] + 16
            tag_pills.append((tname, tw_t))

        row_tags = []
        row_w = 0
        for tag, tw_t in tag_pills:
            if row_w + tw_t > W - 40:
                break
            row_tags.append((tag, tw_t))
            row_w += tw_t + 8

        total_row_w = sum(tw for _, tw in row_tags) + (len(row_tags) - 1) * 8
        x_start = (W - total_row_w) // 2
        x_cur = x_start
        for tag, tw_t in row_tags:
            draw.rounded_rectangle(
                [x_cur, tag_y, x_cur + tw_t, tag_y + 26],
                radius=13, fill=CLR_TAG_BG
            )
            bbox_t = draw.textbbox((0, 0), tag, font=fnt_xs)
            tw_str = bbox_t[2] - bbox_t[0]
            draw.text((x_cur + (tw_t - tw_str) // 2, tag_y + 5), tag, font=fnt_xs, fill=(26, 58, 92))
            x_cur += tw_t + 8

    # ── 二维码 ──
    card_url = f'https://asiamlhk.com/pub/{profile_uuid}'
    qr = qrcode.QRCode(version=3, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=6, border=1)
    qr.add_data(card_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color='white', back_color='white').convert('RGB')
    qr_size = 90
    qr_img = qr_img.resize((qr_size, qr_size), Image.LANCZOS)

    qr_border = Image.new('RGB', (qr_size + 6, qr_size + 6), (255, 255, 255))
    qr_border.paste(qr_img, (3, 3))
    img.paste(qr_border, (W - qr_size - 20, H - qr_size - 20))

    draw.text((W - qr_size - 20, H - qr_size - 32), '微信扫码查看', font=fnt_xs, fill=CLR_GRAY)
    draw.text((W - qr_size - 20, H - qr_size - 20 + qr_size + 4), '→ 加好友', font=fnt_xs, fill=CLR_ORANGE)
    draw.text((20, H - 24), '燃冰 AI商务社交', font=fnt_xs, fill=CLR_GRAY)

    # ── 输出PNG ──
    buf = io.BytesIO()
    img.save(buf, format='PNG', quality=95)
    buf.seek(0)
    return buf.read()


class ProfileViewSet(viewsets.GenericViewSet):
    """Profile相关API"""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Profile.objects.select_related('user').all()

    def get_serializer_class(self):
        if self.action == 'list':
            return ProfileListSerializer
        elif self.action == 'retrieve':
            return ProfileDetailSerializer
        elif self.action in ('me', 'update_me'):
            return ProfileEditSerializer
        elif self.action == 'update_tags':
            return ProfileTagsUpdateSerializer
        elif self.action == 'cert':
            return CertSubmitSerializer
        return ProfileDetailSerializer

    def retrieve(self, request, pk=None):
        try:
            profile = Profile.objects.select_related('user').get(uuid=pk)
        except Profile.DoesNotExist:
            return Response({'code': 2001, 'message': '用户不存在', 'data': None},
                          status=status.HTTP_404_NOT_FOUND)
        return Response({'code': 0, 'data': ProfileDetailSerializer(profile).data})

    def get_object(self):
        """支持UUID查询"""
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        pk = self.kwargs.get(lookup_url_kwarg)
        return Profile.objects.select_related('user').get(uuid=pk)

    def _my_profile(self):
        """获取当前用户的Profile，带DoesNotExist处理"""
        try:
            return Profile.objects.get(user=self.request.user)
        except Profile.DoesNotExist:
            return None

    @action(detail=False, methods=['get', 'put'])
    def me(self, request):
        """获取/编辑当前用户Profile"""
        profile, _ = Profile.objects.get_or_create(
            user=request.user,
            defaults={'real_name': request.user.nickname or '未命名'}
        )
        if request.method == 'GET':
            return Response({'code': 0, 'data': ProfileDetailSerializer(profile).data})

        serializer = ProfileEditSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        # 处理密码修改
        if request.data.get('password'):
            request.user.set_password(request.data['password'])
            request.user.save(update_fields=['password'])
        return Response({'code': 0, 'message': '更新成功'})

    @action(detail=False, methods=['post'])
    def cert(self, request):
        """提交认证申请"""
        profile, _ = Profile.objects.get_or_create(user=request.user)
        serializer = CertSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile.cert_level = serializer.validated_data['cert_level']
        profile.cert_status = 1  # 审核中
        for field in ['education_year', 'education_school', 'education_major', 'cert_document_url']:
            if field in serializer.validated_data:
                setattr(profile, field, serializer.validated_data[field])
        profile.save()
        return Response({'code': 0, 'message': '认证申请已提交，审核结果将在24小时内通知'})

    @action(detail=False, methods=['get'], url_path='me/stats')
    def me_stats(self, request):
        """我的Profile统计"""
        profile, _ = Profile.objects.get_or_create(user=request.user)
        from supplies.models import Supply, Connection
        from django.db.models import Sum
        supply_count = Supply.objects.filter(profile=profile, status=1).count()
        demand_count = Supply.objects.filter(profile=profile, supply_type=2, status=1).count()
        match_count = profile.received_matches.filter(status=1).count()
        conn_count = Connection.objects.filter(user_a=request.user, status=1).count() + \
                     Connection.objects.filter(user_b=request.user, status=1).count()
        return Response({'code': 0, 'data': {
            'conn_count': conn_count,
            'supply_count': supply_count,
            'demand_count': demand_count,
            'match_count': match_count,
            'active_score': float(profile.active_score),
        }})

    @action(detail=False, methods=['post'])
    def update_tags(self, request):
        """更新我的标签"""
        serializer = ProfileTagsUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile, _ = Profile.objects.get_or_create(user=request.user)
        tags_data = serializer.validated_data['tags']
        ProfileTag.objects.filter(profile=profile).delete()
        for item in tags_data:
            ProfileTag.objects.create(
                profile=profile,
                tag_id=item['id'],
                tag_type=item['tag_type'],
                weight=float(item.get('weight', 1.0))
            )
        return Response({'code': 0, 'message': '标签已更新'})

    @action(detail=False, methods=['post'])
    def send_friend_request(self, request):
        """发好友请求（加好友前先发请求）"""
        from supplies.models import FriendRequest

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
        from supplies.models import Connection
        from django.db.models import Q
        if Connection.objects.filter(
            Q(user_a=request.user, user_b=target.user) |
            Q(user_a=target.user, user_b=request.user)
        ).exists():
            return Response({'code': 0, 'message': '你们已经是好友了'})

        # 检查是否已有待处理请求
        my_profile = self._my_profile()
        if not my_profile:
            return Response({'code': 2001, 'message': '用户档案不存在'}, status=status.HTTP_404_NOT_FOUND)
        existing = FriendRequest.objects.filter(
            from_profile=my_profile,
            to_profile=target,
            status=1
        ).first()
        if existing:
            return Response({'code': 0, 'message': '已发送过请求，等待对方接受'})

        fr = FriendRequest.objects.create(
            from_profile=my_profile,
            to_profile=target,
            message=message,
            status=1
        )
        return Response({
            'code': 0,
            'message': '请求已发送',
            'data': {'uuid': str(fr.uuid)}
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def friend_requests(self, request):
        """我收到的加好友请求列表"""
        from supplies.models import FriendRequest
        my_profile = self._my_profile()
        if not my_profile:
            return Response({'code': 2001, 'message': '用户档案不存在'}, status=status.HTTP_404_NOT_FOUND)
        qs = FriendRequest.objects.filter(
            to_profile=my_profile, status=1
        ).select_related('from_profile__user').order_by('-created_at')
        from .serializers import ProfileDetailSerializer
        from supplies.serializers import FriendRequestSerializer
        serializer = FriendRequestSerializer(qs, many=True)
        return Response({'code': 0, 'data': serializer.data})

    @action(detail=False, methods=['post'])
    def accept_friend_request(self, request):
        """接受好友请求"""
        from supplies.models import FriendRequest, Connection

        req_uuid = request.data.get('uuid')
        if not req_uuid:
            return Response({'code': 4001, 'message': '缺少uuid'})

        my_profile = self._my_profile()
        if not my_profile:
            return Response({'code': 2001, 'message': '用户档案不存在'}, status=status.HTTP_404_NOT_FOUND)
        try:
            fr = FriendRequest.objects.get(uuid=req_uuid, to_profile=my_profile, status=1)
        except FriendRequest.DoesNotExist:
            return Response({'code': 4041, 'message': '请求不存在或已处理'})

        # 建立双向好友关系
        Connection.objects.get_or_create(
            user_a=min(fr.from_profile.user_id, fr.to_profile.user_id),
            user_b=max(fr.from_profile.user_id, fr.to_profile.user_id),
            defaults={'conn_type': 1, 'status': 1}
        )
        fr.status = 2  # 已接受
        fr.save()

        # 更新双方的 conn_count
        for profile in [fr.from_profile, fr.to_profile]:
            profile.conn_count = Connection.objects.filter(
                Q(user_a=profile.user, status=1) | Q(user_b=profile.user, status=1)
            ).count()
            profile.save(update_fields=['conn_count'])

        return Response({'code': 0, 'message': '已接受，你们现在是好友了'})

    @action(detail=False, methods=['post'])
    def reject_friend_request(self, request):
        """拒绝好友请求"""
        from supplies.models import FriendRequest

        req_uuid = request.data.get('uuid')
        if not req_uuid:
            return Response({'code': 4001, 'message': '缺少uuid'})

        my_profile = self._my_profile()
        if not my_profile:
            return Response({'code': 2001, 'message': '用户档案不存在'}, status=status.HTTP_404_NOT_FOUND)
        try:
            fr = FriendRequest.objects.get(uuid=req_uuid, to_profile=my_profile, status=1)
        except FriendRequest.DoesNotExist:
            return Response({'code': 4041, 'message': '请求不存在或已处理'})

        fr.status = 3  # 已拒绝
        fr.save()
        return Response({'code': 0, 'message': '已拒绝'})

    @action(detail=False, methods=['post'])
    def connect(self, request):
        """发好友请求（兼容旧名）"""
        return self.send_friend_request(request)

    @action(detail=True, methods=['get'], permission_classes=[])
    def card(self, request, pk=None):
        """生成分享名片PNG图片（CPU密集型，使用线程池避免阻塞主线程）"""
        profile = self.get_object()

        # 收集生成名片所需的数据（避免在后台线程访问ORM对象）
        profile_uuid = str(profile.uuid)
        profile_data = {
            'real_name': profile.real_name,
            'cert_level': profile.cert_level,
            'company': profile.company,
            'position': profile.position,
            'education_school': profile.education_school,
            'education_year': profile.education_year,
        }
        profile_tag_names = list(ProfileTag.objects.filter(
            profile=profile, tag_type__in=[1, 3]
        ).select_related('tag').values_list('tag__name', flat=True)[:6])

        # 提交到线程池执行（PIL释放GIL，不影响其他线程）
        future = _card_executor.submit(
            _generate_card_image, profile_uuid, profile_data, profile_tag_names
        )
        png_bytes = future.result()
        return HttpResponse(png_bytes, content_type='image/png')

    @action(detail=False, methods=['get'])
    def tags_tree(self, request):
        """获取标签树（L1~L5）"""
        tags = Tag.objects.all()
        # 简化为L1+L2两级
        tree = {}
        for tag in tags:
            l1 = tag.l1_category
            if l1 not in tree:
                tree[l1] = {}
            l2 = tag.l2_group or '其他'
            if l2 not in tree[l1]:
                tree[l1][l2] = []
            tree[l1][l2].append({'id': tag.id, 'name': tag.name, 'tag_type': tag.tag_type})
        return Response({'code': 0, 'data': tree})

    @action(detail=False, methods=['post'])
    def send_message(self, request):
        """发私信"""
        from .models import PrivateMessage

        target_uuid = request.data.get('target_uuid')
        content = request.data.get('content', '').strip()
        if not target_uuid:
            return Response({'code': 4001, 'message': '缺少target_uuid'})
        if not content:
            return Response({'code': 4002, 'message': '消息内容不能为空'})

        try:
            target = Profile.objects.get(uuid=target_uuid)
        except Profile.DoesNotExist:
            return Response({'code': 2001, 'message': '用户不存在'})

        if target.user == request.user:
            return Response({'code': 4003, 'message': '不能给自己发消息'})

        my_profile = self._my_profile()
        if not my_profile:
            return Response({'code': 2001, 'message': '用户档案不存在'}, status=status.HTTP_404_NOT_FOUND)
        msg = PrivateMessage.objects.create(
            from_profile=my_profile,
            to_profile=target,
            content=content
        )
        return Response({
            'code': 0,
            'message': '发送成功',
            'data': {'uuid': str(msg.uuid)}
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def conversations(self, request):
        """会话列表（所有好友+最新消息+未读数）"""
        from .models import PrivateMessage

        my_profile = self._my_profile()
        if not my_profile:
            return Response({'code': 2001, 'message': '用户档案不存在'}, status=status.HTTP_404_NOT_FOUND)
        # 找出所有与我有关的消息对应的对方profile
        msg_profiles = list(PrivateMessage.objects.filter(
            from_profile=my_profile
        ).values_list('to_profile', flat=True).distinct())
        msg_profiles_b = list(PrivateMessage.objects.filter(
            to_profile=my_profile
        ).values_list('from_profile', flat=True).distinct())

        all_peer_ids = set(msg_profiles) | set(msg_profiles_b)
        conversations = []
        for peer_id in all_peer_ids:
            peer = Profile.objects.get(id=peer_id)
            # 分别查发送和接收，取最新一条
            sent = PrivateMessage.objects.filter(
                from_profile=my_profile, to_profile=peer
            ).order_by('-created_at').first()
            received = PrivateMessage.objects.filter(
                from_profile=peer, to_profile=my_profile
            ).order_by('-created_at').first()
            last_msg = sent if (sent and received is None or sent and received and sent.created_at >= received.created_at) else received
            unread = PrivateMessage.objects.filter(
                from_profile=peer, to_profile=my_profile, is_read=False
            ).count()
            conversations.append({
                'peer': peer,
                'last_message': last_msg,
                'unread_count': unread
            })

        conversations.sort(
            key=lambda x: x['last_message'].created_at if x['last_message'] else timezone.make_aware(timezone.datetime.min),
            reverse=True
        )
        from .serializers import ConversationSerializer
        serializer = ConversationSerializer(conversations, many=True)
        return Response({'code': 0, 'data': serializer.data})

    @action(detail=False, methods=['get'])
    def messages_with(self, request):
        """与某个好友的消息历史"""
        from .models import PrivateMessage

        target_uuid = request.GET.get('target_uuid')
        if not target_uuid:
            return Response({'code': 4001, 'message': '缺少target_uuid'})

        try:
            target = Profile.objects.get(uuid=target_uuid)
        except Profile.DoesNotExist:
            return Response({'code': 2001, 'message': '用户不存在'})

        my_profile = self._my_profile()
        if not my_profile:
            return Response({'code': 2001, 'message': '用户档案不存在'}, status=status.HTTP_404_NOT_FOUND)
        sent = list(PrivateMessage.objects.filter(
            from_profile=my_profile, to_profile=target
        ).order_by('created_at'))
        received = list(PrivateMessage.objects.filter(
            from_profile=target, to_profile=my_profile
        ).order_by('created_at'))
        msgs = sorted(sent + received, key=lambda m: m.created_at)

        # 标记对方发的消息为已读
        PrivateMessage.objects.filter(
            from_profile=target, to_profile=my_profile, is_read=False
        ).update(is_read=True)

        from .serializers import PrivateMessageSerializer
        serializer = PrivateMessageSerializer(msgs, many=True)
        return Response({'code': 0, 'data': serializer.data})


class ContactTagViewSet(viewsets.GenericViewSet):
    """联系人标签API"""
    permission_classes = [IsAuthenticated]

    def _my_profile(self):
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        return profile

    def list(self, request):
        """我的所有联系人标签"""
        profile = self._my_profile()
        tags = ContactTag.objects.filter(owner=profile)
        return Response({'code': 0, 'data': ContactTagSerializer(tags, many=True).data})

    def create(self, request):
        """创建新标签"""
        name = request.data.get('name', '').strip()
        if not name:
            return Response({'code': 4001, 'message': '标签名不能为空'})
        profile = self._my_profile()
        tag, created = ContactTag.objects.get_or_create(owner=profile, name=name)
        return Response({'code': 0, 'data': ContactTagSerializer(tag).data}, status=status.HTTP_201_CREATED)

    def destroy(self, request, pk=None):
        """删除标签"""
        profile = self._my_profile()
        try:
            tag = ContactTag.objects.get(id=pk, owner=profile)
        except ContactTag.DoesNotExist:
            return Response({'code': 4041, 'message': '标签不存在'}, status=status.HTTP_404_NOT_FOUND)
        tag.delete()
        return Response({'code': 0, 'message': '已删除'})

    @action(detail=False, methods=['get'], url_path='contacts/(?P<profile_uuid>[^/]+)/tags')
    def contact_tags(self, request, profile_uuid=None):
        """获取某联系人的标签"""
        profile = self._my_profile()
        try:
            target = Profile.objects.get(uuid=profile_uuid)
        except Profile.DoesNotExist:
            return Response({'code': 2001, 'message': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)
        relations = ContactTagRelation.objects.filter(
            contact_tag__owner=profile, contact_profile=target
        ).select_related('contact_tag')
        return Response({'code': 0, 'data': ContactTagSerializer([r.contact_tag for r in relations], many=True).data})

    @action(detail=False, methods=['post'], url_path='contacts/(?P<profile_uuid>[^/]+)/tags/add')
    def add_contact_tag(self, request, profile_uuid=None):
        """给联系人添加标签"""
        profile = self._my_profile()
        tag_id = request.data.get('tag_id')
        if not tag_id:
            return Response({'code': 4001, 'message': '缺少tag_id'})
        try:
            target = Profile.objects.get(uuid=profile_uuid)
            tag = ContactTag.objects.get(id=tag_id, owner=profile)
        except (Profile.DoesNotExist, ContactTag.DoesNotExist):
            return Response({'code': 2001, 'message': '用户或标签不存在'}, status=status.HTTP_404_NOT_FOUND)
        rel, created = ContactTagRelation.objects.get_or_create(contact_tag=tag, contact_profile=target)
        return Response({'code': 0, 'message': '已添加' if created else '标签已存在'})

    @action(detail=True, methods=['delete'], url_path='contacts/(?P<profile_uuid>[^/]+)/tags/(?P<tag_id>[^/]+)')
    def remove_contact_tag(self, request, profile_uuid=None, tag_id=None):
        """移除联系人的标签"""
        profile = self._my_profile()
        try:
            target = Profile.objects.get(uuid=profile_uuid)
            tag = ContactTag.objects.get(id=tag_id, owner=profile)
            rel = ContactTagRelation.objects.get(contact_tag=tag, contact_profile=target)
            rel.delete()
        except (Profile.DoesNotExist, ContactTag.DoesNotExist, ContactTagRelation.DoesNotExist):
            return Response({'code': 2001, 'message': '关系不存在'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'code': 0, 'message': '已移除'})


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """标签只读API"""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
