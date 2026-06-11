"""Network graph and alumni filter views."""
import math
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from profiles.models import Profile
from supplies.models import Connection


class NetworkGraphView(LoginRequiredMixin, TemplateView):
    template_name = 'pages/network_graph.html'
    login_url = '/pages/login/'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        profile, _ = Profile.objects.get_or_create(user=user)
        ctx['profile'] = profile

        # ── 直接连接 ──
        my_conns_a = list(Connection.objects.filter(user_a=user, status=1).select_related('user_b__profile'))
        my_conns_b = list(Connection.objects.filter(user_b=user, status=1).select_related('user_a__profile'))

        direct_profiles = []
        seen_ids = set()
        for c in my_conns_a + my_conns_b:
            p = c.user_b.profile if c.user_a == user else c.user_a.profile
            if p.id not in seen_ids:
                seen_ids.add(p.id)
                p._conn_type = c.conn_type
                direct_profiles.append(p)

        ctx['connection_count'] = len(direct_profiles)
        ctx['direct_connections'] = direct_profiles[:12]

        # ── 二度人脉 ──
        conn_user_ids = {c.user_b_id for c in my_conns_a} | {c.user_a_id for c in my_conns_b}
        candidates = Profile.objects.select_related('user').exclude(
            user_id__in=conn_user_ids | {user.id}
        ).exclude(user=user)[:20]

        def calc_mutual(p):
            p_conns = set(
                list(Connection.objects.filter(user_a=p.user, status=1).values_list('user_b_id', flat=True)) +
                list(Connection.objects.filter(user_b=p.user, status=1).values_list('user_a_id', flat=True))
            )
            return len(p_conns & conn_user_ids)

        second_degree = []
        for p in candidates:
            mc = calc_mutual(p)
            if mc > 0:
                p.mutual_count = mc
                second_degree.append(p)
        second_degree.sort(key=lambda x: -x.mutual_count)
        ctx['second_degree'] = second_degree[:8]
        ctx['second_degree_count'] = Profile.objects.exclude(
            user_id__in=conn_user_ids | {user.id}
        ).exclude(user=user).count()

        # ── 三度人脉（估算） ──
        second_ids = {p.user_id for p in second_degree}
        third_count = Profile.objects.exclude(
            user_id__in=conn_user_ids | second_ids | {user.id}
        ).exclude(user=user).count()
        ctx['third_degree_count'] = third_count

        # ── 图谱节点数据（人脉圈子可视化）──
        colors = ['#e86a3a', '#1a3a5c', '#059669', '#d97706', '#7c3aed', '#0891b2', '#be185d', '#ea580c']
        network_nodes = []
        for i, p in enumerate(direct_profiles[:8]):
            angle = 2 * math.pi * i / max(len(direct_profiles), 1)
            radius = 28
            top = 50 + radius * math.sin(angle)
            left = 50 + radius * math.cos(angle)
            initials_ = (p.real_name[0] if p.real_name else '?').upper()
            network_nodes.append({
                'top': round(top, 1),
                'left': round(left, 1),
                'color': colors[i % len(colors)],
                'initial': initials_,
                'name': p.real_name,
            })
        ctx['network_nodes'] = network_nodes

        return ctx


class AlumniFilterView(LoginRequiredMixin, TemplateView):
    template_name = 'pages/alumni_filter.html'
    login_url = '/pages/login/'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        profile, _ = Profile.objects.get_or_create(user=self.request.user)

        profiles = Profile.objects.select_related('user').exclude(user=self.request.user)

        year_start = self.request.GET.get('year_start', '')
        year_end = self.request.GET.get('year_end', '')
        college = self.request.GET.get('college', '')
        major = self.request.GET.get('major', '')
        province = self.request.GET.get('province', '')
        city = self.request.GET.get('city', '')
        industries_param = self.request.GET.get('industries', '')
        tags_param = self.request.GET.get('tags', '')

        if year_start:
            profiles = profiles.filter(education_year__gte=year_start)
        if year_end:
            profiles = profiles.filter(education_year__lte=year_end)
        if college:
            profiles = profiles.filter(education_school__icontains=college)
        if major:
            profiles = profiles.filter(education_major__icontains=major)
        if province:
            profiles = profiles.filter(location_province__icontains=province)
        if city:
            profiles = profiles.filter(city__icontains=city)
        if industries_param:
            industries_list = [x.strip() for x in industries_param.split(',') if x.strip()]
            if industries_list:
                from django.db.models import Q
                q = Q()
                for ind in industries_list:
                    q |= Q(industry__icontains=ind)
                profiles = profiles.filter(q)
        if tags_param:
            tag_ids = [int(x) for x in tags_param.split(',') if x.strip().isdigit()]
            if tag_ids:
                from profiles.models import ProfileTag
                tagged_profiles = ProfileTag.objects.filter(tag_id__in=tag_ids).values_list('profile_id', flat=True)
                profiles = profiles.filter(id__in=tagged_profiles)

        ctx['profiles'] = profiles.order_by('-user__last_login_at')[:20]

        all_profiles_for_options = Profile.objects.exclude(user=self.request.user)

        years_qs = all_profiles_for_options.exclude(
            education_year=''
        ).values_list('education_year', flat=True).distinct().order_by('-education_year')
        ctx['years'] = list(years_qs)[:30]

        ctx['colleges'] = list(
            all_profiles_for_options.exclude(education_school='')
            .values_list('education_school', flat=True).distinct()[:50]
        )

        major_groups = {}
        for row in all_profiles_for_options.exclude(education_major='').exclude(education_school='').values('education_school', 'education_major').distinct()[:200]:
            school = row['education_school']
            major = row['education_major']
            if school not in major_groups:
                major_groups[school] = []
            if major not in major_groups[school]:
                major_groups[school].append(major)
        import json
        ctx['major_map_json'] = json.dumps(major_groups)

        ctx['provinces'] = list(
            all_profiles_for_options.exclude(location_province='')
            .values_list('location_province', flat=True).distinct()[:50]
        )

        ctx['industries'] = list(
            all_profiles_for_options.exclude(industry='')
            .values_list('industry', flat=True).distinct()[:30]
        )

        from profiles.models import Tag
        ctx['all_tags'] = Tag.objects.filter(is_recommend=True).order_by('-hot_score')[:20]

        ctx['filter_year_start'] = year_start
        ctx['filter_year_end'] = year_end
        ctx['filter_college'] = college
        ctx['filter_major'] = major
        ctx['filter_province'] = province
        ctx['filter_city'] = city
        ctx['filter_industries'] = industries_param
        ctx['filter_tags'] = tags_param

        return ctx
