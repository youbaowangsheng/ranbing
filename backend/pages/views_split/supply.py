"""Supply demand, publish, detail views."""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.http import JsonResponse
from profiles.models import Profile, Tag, ProfileTag
from supplies.models import Supply
from .auth import csrf_exempt


class SupplyDemandView(TemplateView):
    template_name = 'pages/supply_demand.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user

        if user.is_authenticated:
            my_profile = Profile.objects.get_or_create(user=user)[0]
        else:
            my_profile = None

        supply_type = self.request.GET.get('type')
        tag_id = self.request.GET.get('tag')

        qs = Supply.objects.select_related('profile__user').filter(status=1)

        if my_profile:
            my_supply_tag_ids = ProfileTag.objects.filter(
                profile=my_profile, tag_type=1
            ).values_list('tag_id', flat=True)
            ctx['my_tags'] = Tag.objects.filter(id__in=my_supply_tag_ids)[:12]
        else:
            ctx['my_tags'] = []

        if supply_type:
            qs = qs.filter(supply_type=int(supply_type))

        if tag_id:
            qs = qs.filter(tags__contains=[int(tag_id)])

        all_tag_map = {t.id: t.name for t in Tag.objects.all()}
        supply_list = qs.order_by('-created_at')[:30]
        for s in supply_list:
            s.tag_names = [all_tag_map.get(int(tid), '') for tid in (s.tags or [])]
        ctx['supply_list'] = supply_list
        ctx['current_type'] = supply_type or ''
        ctx['current_tag'] = tag_id or ''
        ctx['current_view'] = self.request.GET.get('view', 'opportunity')
        ctx['profile_uuid'] = str(my_profile.uuid) if my_profile else ''

        ctx['all_tags'] = Tag.objects.filter(is_recommend=True).order_by('-hot_score')[:20]

        return ctx


class PublishSupplyView(LoginRequiredMixin, TemplateView):
    template_name = 'pages/publish_supply.html'
    login_url = '/pages/login/'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['tags'] = Tag.objects.filter(is_recommend=True).order_by('-hot_score')[:30]
        return ctx

    def post(self, request, id=None, **kwargs):
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        supply_type = request.POST.get('supply_type', '1')
        tag_ids = request.POST.getlist('tags')

        if not title:
            return render(request, 'pages/publish_supply.html', {
                'error': '标题不能为空',
                'tags': Tag.objects.filter(is_recommend=True).order_by('-hot_score')[:30],
            })

        profile, _ = Profile.objects.get_or_create(user=request.user)
        Supply.objects.create(
            profile=profile,
            supply_type=int(supply_type),
            title=title,
            content=content,
            tags=[int(t) for t in tag_ids if t.isdigit()],
        )
        return redirect('supply_demand')


class SupplyDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'pages/supply_detail.html'
    login_url = '/pages/login/'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        uuid = kwargs.get('uuid')
        try:
            supply = Supply.objects.select_related('profile__user').get(uuid=uuid)
        except Supply.DoesNotExist:
            supply = None

        ctx['supply'] = supply
        if supply and supply.tags:
            tag_ids = [t for t in supply.tags if isinstance(t, int)]
            ctx['tag_names'] = list(Tag.objects.filter(id__in=tag_ids).values_list('name', flat=True))
        else:
            ctx['tag_names'] = []

        ctx['author_profile'] = supply.profile if supply else None

        my_profile = Profile.objects.get_or_create(user=self.request.user)[0]
        if supply:
            ctx['can_send_message'] = (supply.profile.user != self.request.user)
        else:
            ctx['can_send_message'] = False

        return ctx


@csrf_exempt
def send_supply_message(request, uuid):
    """给供需发布者发送私信"""
    if request.method != 'POST':
        return JsonResponse({'code': 405, 'message': '只支持 POST'})

    if not request.user.is_authenticated:
        return JsonResponse({'code': 401, 'message': '未登录'})

    try:
        supply = Supply.objects.select_related('profile__user').get(uuid=uuid)
    except Supply.DoesNotExist:
        return JsonResponse({'code': 404, 'message': '供需不存在'})

    if supply.profile.user == request.user:
        return JsonResponse({'code': 403, 'message': '不能给自己发私信'})

    content = request.POST.get('content', '').strip()
    if not content:
        return JsonResponse({'code': 400, 'message': '内容不能为空'})

    from profiles.models import PrivateMessage
    my_profile, _ = Profile.objects.get_or_create(user=request.user)
    PrivateMessage.objects.create(
        from_profile=my_profile,
        to_profile=supply.profile,
        content=content,
    )
    return JsonResponse({'code': 0, 'message': '发送成功'})
