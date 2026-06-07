"""Search view."""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.views.generic import TemplateView
from profiles.models import Profile, Tag
from supplies.models import Supply
from activities.models import Activity
from communities.models import Community


class SearchView(LoginRequiredMixin, TemplateView):
    template_name = 'pages/search.html'
    login_url = '/pages/login/'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        q = self.request.GET.get('q', '').strip()
        ctx['q'] = q

        if q:
            profiles = Profile.objects.select_related('user').filter(
                Q(real_name__icontains=q) |
                Q(company__icontains=q) |
                Q(position__icontains=q) |
                Q(industry__icontains=q) |
                Q(education_school__icontains=q)
            )[:10]
            ctx['profiles'] = profiles

            supplies = Supply.objects.select_related('profile__user').filter(
                Q(title__icontains=q) | Q(content__icontains=q),
                status=1
            ).order_by('-created_at')[:10]
            tag_map = {t.id: t.name for t in Tag.objects.all()}
            for s in supplies:
                s.tag_names = [tag_map.get(int(tid), '') for tid in (s.tags or [])]
            ctx['supplies'] = supplies

            activities = Activity.objects.select_related('organizer__user').filter(
                Q(title__icontains=q) | Q(description__icontains=q),
                status__in=[1, 2]
            ).order_by('-start_time')[:6]
            for a in activities:
                a.tag_names = [tag_map.get(int(tid), '') for tid in (a.tags or [])]
            ctx['activities'] = activities

            communities = Community.objects.filter(
                Q(name__icontains=q) | Q(description__icontains=q),
                status=1
            ).order_by('-member_count')[:6]
            ctx['communities'] = communities
        else:
            ctx['profiles'] = []
            ctx['supplies'] = []
            ctx['activities'] = []
            ctx['communities'] = []

        return ctx
