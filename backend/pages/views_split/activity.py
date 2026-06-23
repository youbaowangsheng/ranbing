"""Activity views: list, detail, publish, enrollment."""
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.views.generic import TemplateView, ListView
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.shortcuts import render, redirect
from profiles.models import Profile, Tag
from activities.models import Activity, ActivityEnrollment


class ActivityListView(ListView):
    template_name = 'pages/activity_list.html'
    context_object_name = 'activity_list'
    paginate_by = 20

    def get_queryset(self):
        qs = Activity.objects.select_related('organizer__user').filter(status=1).order_by('-start_time')
        tag = self.request.GET.get('tag')
        if tag:
            qs = qs.filter(tags__contains=[int(tag)])
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['tags'] = Tag.objects.filter(is_recommend=True)[:15]
        return ctx


class ActivityDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'pages/activity_detail.html'
    login_url = '/pages/login/'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        activity_id = self.kwargs.get('id')
        try:
            activity = Activity.objects.select_related('organizer__user').get(id=activity_id)
        except Activity.DoesNotExist:
            activity = None
        ctx['activity'] = activity

        if activity:
            all_tag_map = {t.id: t.name for t in Tag.objects.all()}
            activity.tag_names = [all_tag_map.get(int(tid), '') for tid in (activity.tags or [])]

            profile, _ = Profile.objects.get_or_create(user=self.request.user)
            ctx['user_enrollment'] = ActivityEnrollment.objects.filter(
                activity=activity, profile=profile
            ).first()

            enrollments = ActivityEnrollment.objects.filter(
                activity=activity, enrollment_status__in=[1, 2]
            ).select_related('profile__user')
            ctx['enrollments'] = enrollments
            ctx['enrolled_profiles'] = [e.profile for e in enrollments[:8]]

        return ctx


class PublishActivityView(LoginRequiredMixin, TemplateView):
    template_name = 'pages/publish_activity.html'
    login_url = '/pages/login/'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['tags'] = Tag.objects.filter(is_recommend=True).order_by('-hot_score')[:20]
        return ctx

    def post(self, request, id=None, **kwargs):
        title = request.POST.get('title', '').strip()
        if not title:
            return render(request, 'pages/publish_activity.html', {
                'error': '标题不能为空',
                'tags': Tag.objects.filter(is_recommend=True).order_by('-hot_score')[:20],
            })
        profile, _ = Profile.objects.get_or_create(user=request.user)
        tag_ids = [int(t) for t in request.POST.getlist('tags') if t.isdigit()]
        Activity.objects.create(
            organizer=profile,
            title=title,
            description=request.POST.get('description', ''),
            activity_type=int(request.POST.get('activity_type', 1)),
            host_school=request.POST.get('host_school', ''),
            location=request.POST.get('location', ''),
            start_time=request.POST.get('start_time') or None,
            end_time=request.POST.get('end_time') or None,
            max_attendees=int(request.POST.get('max_attendees', 100)),
            fee=request.POST.get('fee') or '0',
            tags=tag_ids,
        )
        return redirect('activity_list')


@csrf_exempt
@login_required(login_url='/pages/login/')
def enroll_activity(request, id):
    """POST-only: 报名活动"""
    try:
        activity = Activity.objects.get(id=id)
    except Activity.DoesNotExist:
        return JsonResponse({'code': 2001, 'message': '活动不存在'})

    if activity.status != 1:
        return JsonResponse({'code': 2002, 'message': '活动不在报名期'})

    profile, _ = Profile.objects.get_or_create(user=request.user)
    enrollment, created = ActivityEnrollment.objects.get_or_create(
        activity=activity, profile=profile,
        defaults={'enrollment_status': 1}
    )
    if not created:
        return JsonResponse({'code': 2003, 'message': '您已报名过该活动'})

    activity.current_attendees = ActivityEnrollment.objects.filter(
        activity=activity, enrollment_status__in=[1, 2]
    ).count()
    activity.save(update_fields=['current_attendees'])

    return JsonResponse({'code': 0, 'message': '报名成功'})


@csrf_exempt
@login_required(login_url='/pages/login/')
def cancel_enrollment(request, id):
    """POST-only: 取消活动报名"""
    try:
        activity = Activity.objects.get(id=id)
    except Activity.DoesNotExist:
        return JsonResponse({'code': 2001, 'message': '活动不存在'})

    profile, _ = Profile.objects.get_or_create(user=request.user)
    enrollment = ActivityEnrollment.objects.filter(
        activity=activity, profile=profile, enrollment_status__in=[1, 2]
    ).first()
    if not enrollment:
        return JsonResponse({'code': 2003, 'message': '您未报名该活动'})

    enrollment.enrollment_status = 3
    enrollment.save()

    activity.current_attendees = ActivityEnrollment.objects.filter(
        activity=activity, enrollment_status__in=[1, 2]
    ).count()
    activity.save(update_fields=['current_attendees'])

    return JsonResponse({'code': 0, 'message': '已取消报名'})
