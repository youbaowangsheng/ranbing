"""Community views: list, detail, join."""
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.views.generic import TemplateView
from django.shortcuts import redirect
from profiles.models import Profile
from communities.models import Community, CommunityMember, Message


class CommunityView(TemplateView):
    template_name = 'pages/community.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user

        if user.is_authenticated:
            profile, _ = Profile.objects.get_or_create(user=user)
            my_memberships = CommunityMember.objects.filter(
                profile=profile, status=1
            ).select_related('community')
            ctx['my_communities'] = [m.community for m in my_memberships]
            my_joined_ids = set(CommunityMember.objects.filter(
                profile=profile, status=1
            ).values_list('community_id', flat=True))
            ctx['my_joined_ids'] = my_joined_ids
        else:
            ctx['my_communities'] = []
            ctx['my_joined_ids'] = set()

        ctx['community_list'] = Community.objects.filter(status=1).order_by('-member_count')[:20]
        return ctx


@method_decorator(csrf_exempt, name='dispatch')
class CommunityDetailView(TemplateView):
    template_name = 'pages/community_detail.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        community_id = self.kwargs.get('id')
        try:
            community = Community.objects.select_related('owner__user').get(id=community_id)
        except Community.DoesNotExist:
            community = None
        ctx['community'] = community

        if community:
            if self.request.user.is_authenticated:
                profile, _ = Profile.objects.get_or_create(user=self.request.user)
                my_membership = CommunityMember.objects.filter(
                    community=community, profile=profile, status=1
                ).first()
                ctx['my_membership'] = my_membership
            else:
                ctx['my_membership'] = None

            members = CommunityMember.objects.filter(
                community=community, status=1
            ).select_related('profile__user')[:20]
            ctx['members'] = members

            messages = Message.objects.filter(
                community=community
            ).select_related('profile__user').order_by('-created_at')[:30]
            ctx['messages'] = list(reversed(messages))
        else:
            ctx['my_membership'] = None
            ctx['members'] = []
            ctx['messages'] = []
        return ctx

    def post(self, request, id=None, **kwargs):
        community_id = self.kwargs.get('id')
        try:
            community = Community.objects.get(id=community_id)
        except Community.DoesNotExist:
            return JsonResponse({'code': 2001, 'message': '社群不存在'})

        profile, _ = Profile.objects.get_or_create(user=request.user)
        membership = CommunityMember.objects.filter(
            community=community, profile=profile, status=1
        ).first()
        if not membership:
            return JsonResponse({'code': 2003, 'message': '请先加入社群'})

        content = request.POST.get('content', '').strip()
        if not content:
            return JsonResponse({'code': 2002, 'message': '内容不能为空'})

        Message.objects.create(
            community=community,
            profile=profile,
            content=content,
            msg_type=1,
        )
        return redirect('community_detail', id=community_id)


@csrf_exempt
@login_required(login_url='/pages/login/')
def join_community(request, id):
    """POST-only: 加入社群"""
    try:
        community = Community.objects.get(id=id)
    except Community.DoesNotExist:
        return JsonResponse({'code': 2001, 'message': '社群不存在'})

    profile, _ = Profile.objects.get_or_create(user=request.user)
    member, created = CommunityMember.objects.get_or_create(
        community=community, profile=profile,
        defaults={'role': 1, 'status': 1}
    )
    if not created and member.status == 1:
        return JsonResponse({'code': 2003, 'message': '您已在社群中'})
    if member.status != 1:
        member.status = 1
        member.save()

    community.member_count = CommunityMember.objects.filter(
        community=community, status=1
    ).count()
    community.save(update_fields=['member_count'])

    return JsonResponse({'code': 0, 'message': '加入成功'})
