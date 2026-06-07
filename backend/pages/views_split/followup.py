"""Followup views."""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.generic import TemplateView
from profiles.models import Profile
from supplies.models import Followup


class FollowupView(LoginRequiredMixin, TemplateView):
    template_name = 'pages/followup.html'
    login_url = '/pages/login/'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        profile, _ = Profile.objects.get_or_create(user=self.request.user)

        followups = Followup.objects.filter(
            from_profile=profile
        ).select_related('to_profile__user').order_by('-scheduled_at')[:30]

        followup_list = []
        for f in followups:
            trigger_map = {1: '刚匹配', 2: '活动结束', 3: '社群互动', 4: '自定义'}
            status_map = {0: 'pending', 1: '已计划', 2: '已发送', 3: '已完成'}
            followup_list.append({
                'uuid': f.uuid,
                'to_profile': f.to_profile,
                'trigger_event': trigger_map.get(f.trigger_event, '自定义'),
                'ai_script': f.ai_script,
                'followup_type': f.followup_type,
                'scheduled_at': f.scheduled_at,
                'sent_at': f.sent_at,
                'status': status_map.get(f.status, 'pending'),
                'created_at': f.created_at,
                'is_ai': f.followup_type == 1,
            })

        ctx['followups'] = followup_list

        total = len(followup_list)
        pending = len([f for f in followup_list if f['status'] in ('pending', '已计划')])
        done = len([f for f in followup_list if f['status'] in ('已完成', '已发送')])
        ctx['ai_summary'] = {
            'status': f'{done}已完成 · {pending}进行中' if total else '暂无跟进',
            'summary': f'共 {total} 条跟进记录，其中 {pending} 条待执行。AI 会根据您的校友互动自动生成跟进建议。' if total else '开始和校友互动后，AI 会自动为您生成跟进建议。',
        }

        return ctx

    def post(self, request, **kwargs):
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        to_uuid = request.POST.get('to_profile_uuid', '').strip()

        if not title or not content:
            return render(request, self.template_name, self.get_context_data())

        profile, _ = Profile.objects.get_or_create(user=request.user)

        to_profile = None
        if to_uuid:
            try:
                to_profile = Profile.objects.get(uuid=to_uuid)
            except Profile.DoesNotExist:
                to_profile = None

        Followup.objects.create(
            from_profile=profile,
            to_profile=to_profile,
            trigger_event=4,
            followup_type=2,
            ai_script=content,
            scheduled_at=timezone.now(),
            status=3,
        )
        return redirect('followup')
