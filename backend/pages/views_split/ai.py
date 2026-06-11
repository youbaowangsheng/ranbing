"""AI views: assistant, chat proxy, tags popup."""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from profiles.models import Profile, ProfileTag
from supplies.models import Supply


class AIAssistantView(LoginRequiredMixin, TemplateView):
    template_name = 'pages/ai_assistant.html'
    login_url = '/pages/login/'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        ctx['profile'] = profile
        ctx['profile_uuid'] = str(profile.uuid)
        my_tags = ProfileTag.objects.filter(profile=profile, tag_type=1).select_related('tag')
        ctx['my_tag_names'] = '、'.join(t.tag.name for t in my_tags[:5]) if my_tags else '暂无'
        ctx['my_supply_count'] = Supply.objects.filter(profile=profile, status=1).count()
        return ctx


class AIChatProxyView(APIView):
    """POST /api/v1/ai/chat/ — AI对话代理（解决浏览器跨域调用FIPAI的问题）"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        import httpx

        user_message = request.data.get('message', '')
        if not user_message:
            return Response({'code': 2002, 'message': 'message不能为空'}, status=400)

        try:
            profile = Profile.objects.get(user=request.user)
            my_tags = list(ProfileTag.objects.filter(profile=profile, tag_type=1).select_related('tag')[:5])
            tag_context = '、'.join(t.tag.name for t in my_tags) if my_tags else '暂无标签'
            context_note = (
                f'\n\n[用户背景] 姓名：{profile.real_name}，'
                f'公司：{profile.company}，职位：{profile.position}，'
                f'标签：{tag_context}。'
            )
            user_message_with_context = user_message + context_note
        except Profile.DoesNotExist:
            user_message_with_context = user_message

        fipai_url = 'https://fipai.cn/api/v1/chat/'
        try:
            with httpx.Client(timeout=30) as client:
                resp = client.post(
                    fipai_url,
                    json={'message': user_message_with_context},
                    headers={'Content-Type': 'application/json'}
                )
                resp.raise_for_status()
                data = resp.json()
                return Response({
                    'code': 0,
                    'data': {
                        'content': data.get('content', data.get('reply', '暂无回复')),
                        'channel': data.get('channel', 'fipai'),
                        'metadata': data.get('metadata', {})
                    }
                })
        except httpx.TimeoutException:
            return Response({'code': 5001, 'message': 'AI服务响应超时，请稍后重试'}, status=504)
        except httpx.HTTPStatusError as e:
            return Response({'code': 5002, 'message': f'AI服务错误: {e.response.status_code}'}, status=502)
        except Exception as e:
            return Response({'code': 5000, 'message': f'请求失败: {str(e)}'}, status=500)


class AITagsPopupView(LoginRequiredMixin, TemplateView):
    template_name = 'pages/ai_tags_popup.html'
    login_url = '/pages/login/'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        ctx['profile'] = profile

        all_tags = Tag.objects.filter(is_recommend=True).order_by('l1_category', '-hot_score')
        ctx['tag_categories'] = {}
        for t in all_tags:
            grp = t.l1_category or '其他'
            if grp not in ctx['tag_categories']:
                ctx['tag_categories'][grp] = []
            ctx['tag_categories'][grp].append(t)

        my_tag_ids = set(ProfileTag.objects.filter(profile=profile, tag_type=1).values_list('tag_id', flat=True))
        if my_tag_ids:
            related_tag_ids = ProfileTag.objects.filter(
                profile_id__in=ProfileTag.objects.filter(tag_id__in=my_tag_ids).values_list('profile_id', flat=True),
                tag_id__not_in=my_tag_ids,
                tag__is_recommend=True
            ).values_list('tag_id', flat=True)
            ctx['recommended_tags'] = Tag.objects.filter(id__in=related_tag_ids).order_by('-hot_score')[:10]
        else:
            ctx['recommended_tags'] = Tag.objects.filter(is_recommend=True).order_by('-hot_score')[:10]

        ctx['ai_analysis'] = '基于您的职业背景和历史供需记录，我们推荐以下标签，这些标签能提高您内容的曝光度和匹配精度。'
        return ctx
