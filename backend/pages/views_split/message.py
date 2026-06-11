"""Private message list and detail views."""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from profiles.models import Profile, PrivateMessage


class MessageListView(LoginRequiredMixin, TemplateView):
    """私信列表页"""
    template_name = 'pages/message_list.html'
    login_url = '/pages/login/'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        my_profile, _ = Profile.objects.get_or_create(user=self.request.user)

        sent = list(PrivateMessage.objects.filter(from_profile=my_profile).values_list('to_profile_id', flat=True))
        received = list(PrivateMessage.objects.filter(to_profile=my_profile).values_list('from_profile_id', flat=True))
        counterpart_ids = set(sent + received)

        conversations = []
        for pid in counterpart_ids:
            if not pid:
                continue
            try:
                other = Profile.objects.select_related('user').get(id=pid)
            except Profile.DoesNotExist:
                continue

            latest = PrivateMessage.objects.filter(
                Q(from_profile=my_profile, to_profile=other) |
                Q(from_profile=other, to_profile=my_profile)
            ).order_by('-created_at').first()

            unread = PrivateMessage.objects.filter(
                from_profile=other, to_profile=my_profile, is_read=False
            ).count()

            conversations.append({
                'profile': other,
                'latest_message': latest,
                'unread_count': unread,
            })

        conversations.sort(key=lambda x: x['latest_message'].created_at if x['latest_message'] else '', reverse=True)
        ctx['conversations'] = conversations
        return ctx


class MessageDetailView(LoginRequiredMixin, TemplateView):
    """私信会话详情页"""
    template_name = 'pages/message_detail.html'
    login_url = '/pages/login/'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        uuid = kwargs.get('uuid')
        my_profile, _ = Profile.objects.get_or_create(user=self.request.user)

        try:
            other_profile = Profile.objects.select_related('user').get(uuid=uuid)
        except Profile.DoesNotExist:
            ctx['error'] = '用户不存在'
            ctx['messages'] = []
            ctx['other_profile'] = None
            return ctx

        ctx['other_profile'] = other_profile

        messages = PrivateMessage.objects.filter(
            Q(from_profile=my_profile, to_profile=other_profile) |
            Q(from_profile=other_profile, to_profile=my_profile)
        ).order_by('created_at')

        messages.filter(to_profile=my_profile, is_read=False).update(is_read=True)

        ctx['messages'] = list(messages)
        ctx['my_profile'] = my_profile
        return ctx


@csrf_exempt
def send_message(request):
    """发送私信 AJAX 接口"""
    if request.method != 'POST':
        return JsonResponse({'code': 405, 'message': '只支持 POST'})

    if not request.user.is_authenticated:
        return JsonResponse({'code': 401, 'message': '未登录'})

    target_uuid = request.POST.get('uuid', '').strip()
    content = request.POST.get('content', '').strip()

    if not target_uuid or not content:
        return JsonResponse({'code': 400, 'message': '参数不完整'})

    my_profile, _ = Profile.objects.get_or_create(user=request.user)

    try:
        other_profile = Profile.objects.get(uuid=target_uuid)
    except Profile.DoesNotExist:
        return JsonResponse({'code': 404, 'message': '用户不存在'})

    if other_profile.user == request.user:
        return JsonResponse({'code': 403, 'message': '不能给自己发私信'})

    PrivateMessage.objects.create(
        from_profile=my_profile,
        to_profile=other_profile,
        content=content,
    )
    return JsonResponse({'code': 0, 'message': '发送成功'})
