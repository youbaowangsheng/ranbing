"""Home page view."""
from django.views.generic import TemplateView
from profiles.models import Profile, Tag
from supplies.models import Supply, FriendRequest


class HomeView(TemplateView):
    template_name = 'pages/home.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user

        if user.is_authenticated:
            profile, _ = Profile.objects.get_or_create(
                user=user,
                defaults={
                    'real_name': user.nickname or f'用户{user.phone[-4:]}',
                    'cert_level': 1,
                }
            )
            profile.avatar_bg = 'linear-gradient(135deg,#e86a3a,#f0a06a)'
            ctx['my_profile'] = profile

            ctx['recommended_profiles'] = Profile.objects.select_related('user').exclude(
                user=user
            ).order_by('-user__last_login_at')[:4]

            ctx['friend_request_count'] = FriendRequest.objects.filter(
                to_profile=profile, status=1
            ).count()
        else:
            ctx['my_profile'] = None
            ctx['recommended_profiles'] = Profile.objects.select_related('user').order_by('-user__last_login_at')[:4]
            ctx['friend_request_count'] = 0

        supply_list = Supply.objects.select_related(
            'profile__user'
        ).filter(status=1).order_by('-created_at')[:4]
        all_tag_map = {t.id: t.name for t in Tag.objects.all()}
        for s in supply_list:
            s.tag_names = [all_tag_map.get(int(tid), '') for tid in (s.tags or [])]
        ctx['supply_list'] = supply_list

        from activities.models import Activity
        activity_list = Activity.objects.select_related(
            'organizer__user'
        ).filter(status=1).order_by('-start_time')[:3]
        for a in activity_list:
            a.tag_names = [all_tag_map.get(int(tid), '') for tid in (a.tags or [])]
        ctx['activities'] = activity_list

        all_tags = Tag.objects.filter(is_recommend=True).order_by('-hot_score')[:20]
        ctx['tags'] = all_tags
        ctx['tags_dict'] = {t.id: t for t in all_tags}

        return ctx
