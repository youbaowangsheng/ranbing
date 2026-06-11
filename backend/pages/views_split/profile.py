"""Profile views: view, public, settings, edit, preview, work history, tags, certification."""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.db.models import Q
from django.views.generic import TemplateView
from profiles.models import Profile, Tag, ProfileTag
from supplies.models import Supply


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'pages/profile_view.html'
    login_url = '/pages/login/'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        uuid = self.kwargs.get('uuid')

        if uuid:
            profile = Profile.objects.select_related('user').get(uuid=uuid)
        else:
            profile = Profile.objects.select_related('user').get(user=self.request.user)

        ctx['view_profile'] = profile
        ctx['is_mine'] = (profile.user_id == self.request.user.id)
        ctx['is_connected'] = False
        if not ctx['is_mine']:
            from supplies.models import Connection
            ctx['is_connected'] = Connection.objects.filter(
                Q(user_a=self.request.user, user_b=profile.user) |
                Q(user_a=profile.user, user_b=self.request.user)
            ).exists()

        ctx['my_tags'] = ProfileTag.objects.filter(
            profile=profile, tag_type=1
        ).select_related('tag').values_list('tag__name', flat=True)[:20]

        ctx['my_supplies'] = Supply.objects.filter(profile=profile, status=1).order_by('-created_at')[:10]

        return ctx


class PublicProfileView(TemplateView):
    """公开名片页，无需登录，微信扫码直接访问"""
    template_name = 'pages/pub_profile.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        uuid = self.kwargs.get('uuid')
        try:
            profile = Profile.objects.select_related('user').get(uuid=uuid)
        except Profile.DoesNotExist:
            ctx['not_found'] = True
            return ctx

        ctx['pub_profile'] = profile
        ctx['my_tags'] = ProfileTag.objects.filter(
            profile=profile, tag_type__in=[1, 3]
        ).select_related('tag').values_list('tag__name', flat=True)[:12]
        ctx['supply_count'] = Supply.objects.filter(profile=profile, status=1).count()

        if self.request.user.is_authenticated:
            ctx['is_logged_in'] = True
            try:
                my_profile = Profile.objects.get(user=self.request.user)
                target_profile = profile
                from supplies.models import Connection, FriendRequest

                ctx['is_friend'] = Connection.objects.filter(
                    Q(user_a=self.request.user, user_b=target_profile.user) |
                    Q(user_a=target_profile.user, user_b=self.request.user)
                ).exists()

                ctx['has_pending_request'] = FriendRequest.objects.filter(
                    from_profile=my_profile,
                    to_profile=target_profile,
                    status=1
                ).exists()

                ctx['already_sent_request'] = FriendRequest.objects.filter(
                    from_profile=target_profile,
                    to_profile=my_profile,
                    status=1
                ).exists()
            except Exception:
                ctx['is_friend'] = False
                ctx['has_pending_request'] = False
                ctx['already_sent_request'] = False
        else:
            ctx['is_logged_in'] = False
            ctx['is_friend'] = False
            ctx['has_pending_request'] = False
            ctx['already_sent_request'] = False

        return ctx


class ProfileSettingsView(LoginRequiredMixin, TemplateView):
    template_name = 'pages/profile_settings.html'
    login_url = '/pages/login/'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        profile, _ = Profile.objects.get_or_create(user=user)
        ctx['my_profile'] = profile

        all_tags = Tag.objects.filter(is_recommend=True).order_by('-hot_score')[:50]
        ctx['all_tags'] = all_tags

        ctx['my_supply_tag_ids'] = list(ProfileTag.objects.filter(
            profile=profile, tag_type=1
        ).values_list('tag_id', flat=True))

        ctx['my_demand_tag_ids'] = list(ProfileTag.objects.filter(
            profile=profile, tag_type=2
        ).values_list('tag_id', flat=True))

        return ctx

    def post(self, request, id=None, **kwargs):
        user = request.user
        profile, _ = Profile.objects.get_or_create(user=user)

        if request.FILES.get('avatar'):
            profile.avatar = request.FILES.get('avatar')

        profile.real_name = request.POST.get('real_name', '').strip() or profile.real_name
        profile.gender = int(request.POST.get('gender', 0))
        profile.birthday = request.POST.get('birthday') or None
        profile.company = request.POST.get('company', '')[:128]
        profile.position = request.POST.get('position', '')[:128]
        profile.industry = request.POST.get('industry', '')[:64]
        profile.city = request.POST.get('city', '')[:64]
        profile.education_school = request.POST.get('education_school', '')[:128]
        profile.education_year = request.POST.get('education_year', '')[:10]
        profile.education_major = request.POST.get('education_major', '')[:128]
        profile.bio = request.POST.get('bio', '')[:500]
        profile.save()

        supply_tag_ids = [int(t) for t in request.POST.getlist('supply_tags') if t.isdigit()]
        ProfileTag.objects.filter(profile=profile, tag_type=1).delete()
        for tag_id in supply_tag_ids:
            ProfileTag.objects.get_or_create(profile=profile, tag_id=tag_id, tag_type=1)

        demand_tag_ids = [int(t) for t in request.POST.getlist('demand_tags') if t.isdigit()]
        ProfileTag.objects.filter(profile=profile, tag_type=2).delete()
        for tag_id in demand_tag_ids:
            ProfileTag.objects.get_or_create(profile=profile, tag_id=tag_id, tag_type=2)

        ctx = self.get_context_data(**kwargs)
        ctx['success'] = '保存成功'
        return render(request, self.template_name, ctx)


class ProfileEditView(LoginRequiredMixin, TemplateView):
    template_name = 'pages/profile_edit.html'
    login_url = '/pages/login/'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        ctx['profile'] = profile
        ctx['all_tags'] = Tag.objects.filter(is_recommend=True).order_by('-hot_score')[:50]
        ctx['my_tag_ids'] = list(ProfileTag.objects.filter(
            profile=profile, tag_type=1
        ).values_list('tag_id', flat=True))
        return ctx

    def post(self, request, id=None, **kwargs):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        profile.real_name = request.POST.get('real_name', profile.real_name)
        profile.company = request.POST.get('company', '')[:128]
        profile.position = request.POST.get('position', '')[:128]
        profile.industry = request.POST.get('industry', '')[:64]
        profile.city = request.POST.get('city', '')[:64]
        profile.bio = request.POST.get('bio', '')[:500]
        profile.education_school = request.POST.get('education_school', '')[:128]
        profile.education_year = request.POST.get('education_year', '')[:10]
        profile.education_major = request.POST.get('education_major', '')[:128]
        profile.save()
        return redirect('my_profile')


class WorkHistoryView(LoginRequiredMixin, TemplateView):
    template_name = 'pages/work_history.html'
    login_url = '/pages/login/'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        ctx['profile'] = profile
        return ctx


class TagSelectorView(LoginRequiredMixin, TemplateView):
    template_name = 'pages/tag_selector.html'
    login_url = '/pages/login/'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        ctx['profile'] = profile
        all_tags = Tag.objects.filter(is_recommend=True).order_by('l1_category', '-hot_score')
        ctx['all_tags'] = all_tags
        ctx['tag_groups'] = {}
        for t in all_tags:
            grp = t.l1_category or '其他'
            if grp not in ctx['tag_groups']:
                ctx['tag_groups'][grp] = []
            ctx['tag_groups'][grp].append(t)
        ctx['selected_ids'] = list(ProfileTag.objects.filter(
            profile=profile, tag_type=1
        ).values_list('tag_id', flat=True))
        return ctx


class CertificationView(LoginRequiredMixin, TemplateView):
    template_name = 'pages/certification.html'
    login_url = '/pages/login/'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        ctx['profile'] = profile
        ctx['is_mine'] = True
        ctx['certifications'] = []
        return ctx

    def post(self, request):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        school = request.POST.get('education_school', '').strip()
        major = request.POST.get('education_major', '').strip()
        year = request.POST.get('education_year', '').strip()

        if not school:
            ctx = self.get_context_data()
            ctx['error'] = '请填写学校名称'
            return render(request, self.template_name, ctx)

        profile.education_school = school[:128]
        profile.education_major = major[:128]
        profile.education_year = year[:10]
        profile.cert_level = 2
        profile.cert_status = 1
        profile.save()

        ctx = self.get_context_data()
        ctx['success'] = '认证申请已提交，审核结果将在24小时内通知'
        return render(request, self.template_name, ctx)


class ProfilePreviewView(LoginRequiredMixin, TemplateView):
    template_name = 'pages/profile_preview.html'
    login_url = '/pages/login/'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        ctx['profile'] = profile
        ctx['my_tags'] = ProfileTag.objects.filter(
            profile=profile, tag_type=1
        ).select_related('tag').values_list('tag__name', flat=True)[:20]
        ctx['my_supplies'] = Supply.objects.filter(profile=profile, status=1).order_by('-created_at')[:5]
        return ctx
