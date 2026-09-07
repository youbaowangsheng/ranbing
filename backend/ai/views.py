"""AI相关API视图"""
import json
import uuid
import redis
import logging

import httpx
from django.conf import settings
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.views.decorators.csrf import csrf_exempt

from .services.intent import (
    recognize_intent, extract_tags, generate_match_reason,
    generate_introduction_script, generate_followup_script
)

logger = logging.getLogger(__name__)

# DeepSeek 调用 helper（替代 fipai.cn，2026-08-24 修复）
def _call_deepseek(messages, *, temperature=0.7, max_tokens=1000, timeout=30):
    """
    直接调 DeepSeek Chat Completions API
    返回 (success, content_or_error)
    """
    import httpx as _httpx
    api_key = getattr(settings, 'DEEPSEEK_API_KEY', '')
    base_url = getattr(settings, 'DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
    model = getattr(settings, 'DEEPSEEK_MODEL', 'deepseek-chat')
    if not api_key:
        return False, 'DEEPSEEK_API_KEY 未配置'
    payload = {
        'model': model,
        'messages': messages,
        'temperature': temperature,
        'max_tokens': max_tokens,
    }
    try:
        with _httpx.Client(timeout=timeout) as client:
            resp = client.post(
                f'{base_url}/chat/completions',
                json=payload,
                headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
            )
            resp.raise_for_status()
            data = resp.json()
            return True, data['choices'][0]['message']['content']
    except _httpx.TimeoutException:
        return False, 'DeepSeek 请求超时'
    except _httpx.HTTPStatusError as e:
        return False, f'DeepSeek HTTP {e.response.status_code}: {e.response.text[:200]}'
    except Exception as e:
        return False, f'DeepSeek 调用异常: {str(e)[:200]}'




def _calc_match_score(item: dict, profile) -> float:
    """
    计算供需与用户profile的匹配度 0.0-1.0
    后续可升级为向量相似度
    """
    score = 0.5  # 基础分
    tags = item.get('tags', [])
    if tags and profile:
        try:
            from profiles.models import ProfileTag
            my_tag_names = set(
                t.tag.name.lower()
                for t in ProfileTag.objects.filter(profile=profile, tag_type=1).select_related('tag')
                if t.tag
            )
            item_tags = set(t.lower() for t in tags)
            overlap = my_tag_names & item_tags
            if overlap:
                score += 0.3 * min(len(overlap), 3)
        except Exception:
            pass
    return min(score, 0.99)


def _get_mutual_connections(profile) -> dict:
    """
    查询与当前用户有共同连接的其他用户，返回:
    { profile_uuid: [{name, avatar_color, degree}, ...] }
    目前用共同社群判断。后续扩展 Connection 表。
    """
    try:
        from communities.models import CommunityMember

        # 当前用户加入的社群ID列表
        my_comm_ids = list(
            CommunityMember.objects.filter(profile=profile)
            .values_list('community_id', flat=True)
        )
        if not my_comm_ids:
            return {}

        # 找到在这些社群中的其他用户（排除自己）
        other_members = CommunityMember.objects.filter(
            community_id__in=my_comm_ids
        ).exclude(profile=profile).select_related('profile__user')

        # 按profile分组
        from collections import defaultdict
        conn_map = defaultdict(list)
        color_pool = ['#7c3aed', '#e86a3a', '#059669', '#1a3a5c', '#c8a951']

        for member in other_members:
            p = member.profile
            name = p.real_name or getattr(p.user, 'nickname', '') or getattr(p.user, 'username', '')[:1]
            initial = name[0] if name else '?'
            degree = '群主' if member.role == 3 else '社群成员'
            # 构造渐变色字符串，前端可直接用 style="background:gradient"
            gradients = [
                'linear-gradient(135deg,#7c3aed,#a855f7)',
                'linear-gradient(135deg,#e86a3a,#f0a06a)',
                'linear-gradient(135deg,#059669,#34d399)',
                'linear-gradient(135deg,#1a3a5c,#2d5a8a)',
                'linear-gradient(135deg,#c8a951,#e8c84a)',
            ]
            gradient = gradients[hash(name) % len(gradients)]
            conn_map[str(p.uuid)].append({
                'name': name,
                'initial': initial,
                'gradient': gradient,
                'degree': degree,
            })

        # 只保留有共同社群的用户，且每个profile最多3人
        result = {}
        for k, v in conn_map.items():
            result[k] = v[:3]
        return result

    except Exception as e:
        logger.warning(f"[mutual_connections] error: {e}")
        return {}


def _get_redis_client():
    """获取Redis客户端"""
    redis_url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
    try:
        return redis.from_url(redis_url, decode_responses=True)
    except Exception:
        return None


def _get_session_key(session_id: str) -> str:
    return f"ai:session:{session_id}"


def _load_session(session_id: str) -> list:
    """从Redis加载会话历史，返回[{role, content}, ...]"""
    try:
        client = _get_redis_client()
        raw = client.get(_get_session_key(session_id))
        if raw:
            return json.loads(raw)
    except Exception as e:
        logger.warning(f"[chat-v2] load session error: {e}")
    return []


def _save_session(session_id: str, messages: list, max_msgs: int = 20):
    """保存会话历史到Redis，最多保留max_msgs条"""
    try:
        # 保留最近max_msgs条
        trimmed = messages[-max_msgs:]
        client = _get_redis_client()
        client.set(_get_session_key(session_id), json.dumps(trimmed, ensure_ascii=False), ex=86400 * 7)
    except Exception as e:
        logger.warning(f"[chat-v2] save session error: {e}")


class AIRecognizeIntentView(APIView):
    """POST /ai/recognize-intent — 意图识别"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        text = request.data.get('text', '')
        if not text:
            return Response({'code': 2002, 'message': 'text不能为空'}, status=status.HTTP_400_BAD_REQUEST)
        
        result = recognize_intent(text)
        
        # 构建推荐动作
        intent_redirects = {
            'find_investors': '/pages/supplies?type=1&keyword=投资',
            'find_partners': '/pages/connections/new',
            'publish_supply': '/pages/supplies/publish',
            'find_activity': '/pages/activities',
            'find_community': '/pages/communities',
        }
        suggested_action = {
            'type': 'redirect',
            'target': intent_redirects.get(result.get('intent', ''), '/pages/home')
        }
        
        return Response({
            'code': 0,
            'data': {
                'intent': result.get('intent', 'general_chat'),
                'entities': result.get('entities', {}),
                'suggested_action': suggested_action,
                'reply_text': result.get('reply_text', '我理解了')
            }
        })


class AIExtractTagsView(APIView):
    """POST /ai/extract-tags — 标签提取"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        text = request.data.get('text', '')
        supply_type = request.data.get('supply_type', 1)
        
        if not text:
            return Response({'code': 2002, 'message': 'text不能为空'}, status=status.HTTP_400_BAD_REQUEST)
        
        result = extract_tags(text, int(supply_type))
        
        return Response({
            'code': 0,
            'data': result
        })


class AIMatchView(APIView):
    """POST /ai/match — AI匹配"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        supply_id = request.data.get('supply_id')
        limit = min(int(request.data.get('limit', 20)), 100)
        min_score = float(request.data.get('min_score', 0.5))
        
        from supplies.models import Supply
        from profiles.models import Profile
        
        try:
            supply = Supply.objects.get(id=supply_id)
        except Supply.DoesNotExist:
            return Response({'code': 2001, 'message': '供需不存在'}, status=status.HTTP_404_NOT_FOUND)
        
        # 简单匹配：标签重叠
        user_tags = set(supply.tags)
        candidates = Profile.objects.exclude(id=supply.profile_id).select_related('user')[:200]
        
        matches = []
        for profile in candidates:
            profile_tags = set(pt.tag_id for pt in profile.profile_tags.all())
            overlap = user_tags & profile_tags
            if not overlap:
                continue
            score = min(len(overlap) * 0.2 + 0.5, 0.99)
            if score < min_score:
                continue
            
            # 生成AI理由
            reason_data = generate_match_reason(supply, profile)
            
            matches.append({
                'profile': {
                    'uuid': str(profile.uuid),
                    'real_name': profile.real_name,
                    'company': profile.company,
                    'position': profile.position,
                    'cert_level': profile.cert_level,
                    'avatar_url': profile.user.avatar_url,
                },
                'match_score': reason_data.get('match_score', round(score, 4)),
                'ai_reason': reason_data.get('ai_reason', f'共享{len(overlap)}个标签'),
            })
            if len(matches) >= limit:
                break
        
        # 按分数排序
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        
        return Response({
            'code': 0,
            'data': {
                'matches': matches,
                'total_candidates': candidates.count(),
                'matched_count': len(matches),
            }
        })


class AIGenerateScriptView(APIView):
    """POST /ai/generate-script — AI生成话术"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        script_type = request.data.get('type', 'introduction')
        
        from profiles.models import Profile
        
        from_profile_uuid = request.data.get('from_profile_uuid')
        to_profile_uuid = request.data.get('to_profile_uuid')
        
        try:
            from_profile = Profile.objects.get(uuid=from_profile_uuid)
            to_profile = Profile.objects.get(uuid=to_profile_uuid)
        except Profile.DoesNotExist:
            return Response({'code': 2001, 'message': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)
        
        context = request.data.get('context', {})
        
        if script_type == 'introduction':
            result = generate_introduction_script(from_profile, to_profile, str(context))
        elif script_type == 'followup':
            result = generate_followup_script(from_profile, to_profile, str(context))
        else:
            result = {'script': '请描述您的需求', 'variants': []}
        
        return Response({'code': 0, 'data': result})


class AIChatProxyView(APIView):
    """POST /api/v1/ai/chat/ — AI对话代理"""
    # 需登录，防止匿名无限调用 DeepSeek 烧 API 额度
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_message = request.data.get('message', '')
        if not user_message:
            return Response({'code': 2002, 'message': 'message不能为空'}, status=status.HTTP_400_BAD_REQUEST)

        from django.contrib.auth.models import AnonymousUser
        from profiles.models import Profile, ProfileTag
        try:
            if isinstance(request.user, AnonymousUser):
                raise Profile.DoesNotExist()
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

        DEEPSEEK_API_KEY = getattr(settings, 'DEEPSEEK_API_KEY', '')
        DEEPSEEK_BASE_URL = getattr(settings, 'DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
        DEEPSEEK_MODEL = getattr(settings, 'DEEPSEEK_MODEL', 'deepseek-chat')

        if DEEPSEEK_API_KEY:
            try:
                headers = {
                    'Authorization': f'Bearer {DEEPSEEK_API_KEY}',
                    'Content-Type': 'application/json'
                }
                ds_payload = {
                    'model': DEEPSEEK_MODEL,
                    'messages': [{'role': 'user', 'content': user_message_with_context}],
                    'max_tokens': 500,
                    'temperature': 0.7
                }
                resp = httpx.post(
                    f'{DEEPSEEK_BASE_URL}/chat/completions',
                    json=ds_payload,
                    headers=headers,
                    timeout=30
                )
                resp.raise_for_status()
                data = resp.json()
                content = data.get('choices', [{}])[0].get('message', {}).get('content', '暂无回复')
                return Response({'code': 0, 'data': {'content': content, 'channel': 'deepseek', 'metadata': {}}})
            except httpx.TimeoutException:
                return Response({'code': 5001, 'message': 'AI服务响应超时，请稍后重试'}, status=504)
            except httpx.HTTPStatusError as e:
                return Response({'code': 5002, 'message': f'AI服务错误: {e.response.status_code}'}, status=502)
            except Exception as e:
                return Response({'code': 5000, 'message': f'AI服务暂时不可用: {str(e)}'}, status=500)
        else:
            # No API key: return a helpful demo response
            return Response({
                'code': 0,
                'data': {
                    'content': f'已收到您的消息「{user_message}」，AI功能正在配置中，请联系管理员配置 DeepSeek API Key。',
                    'channel': 'demo',
                    'metadata': {}
                }
            })


class AISupplyMatchesView(APIView):
    """
    GET /api/v1/ai/supply-matches/ — AI供需推荐
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_message = request.query_params.get('message', '')
        session_id = request.query_params.get('session_id', '')

        # 生成或验证session_id
        if not session_id:
            session_id = str(uuid.uuid4())

        # 加载用户profile（仅当前用户，防止 IDOR 枚举他人 PII）
        user_context = ""
        profile = None
        try:
            from profiles.models import Profile, ProfileTag
            profile = Profile.objects.get(user=request.user)

            my_tags = list(
                ProfileTag.objects.filter(profile=profile, tag_type=1)
                .select_related('tag')[:10]
            )
            tag_context = '、'.join(t.tag.name for t in my_tags) if my_tags else '暂无标签'
            user_context = (
                f"根据用户背景，推荐最相关的供需。\n"
                f"用户名：{profile.real_name}，\n"
                f"公司：{profile.company}，\n"
                f"职位：{profile.position}，\n"
                f"行业：{profile.industry}，\n"
                f"城市：{profile.city}，\n"
                f"标签：{tag_context}。"
            )
        except Exception as e:
            logger.warning(f"[supply-matches] load profile error: {e}")
            user_context = "请根据用户需求，推荐最相关的供需项目。"

        # 如果有用户消息，追加到上下文中
        current_user_msg = user_message
        if user_message:
            current_user_msg = user_message + "\n\n" + user_context
        else:
            current_user_msg = user_context

        # 加载会话历史
        history = _load_session(session_id)

        # 构建完整的 messages 数组
        messages = []
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": current_user_msg})

        # 直接调 DeepSeek（替代 fipai.cn，2026-08-24）
        ok, reply_content = _call_deepseek(messages, temperature=0.7, max_tokens=1500, timeout=60)
        if not ok:
            return Response({'code': 5001, 'message': reply_content}, status=502)
        tool_calls = []
        channel = 'deepseek'

        # 更新会话历史
        messages.append({"role": "assistant", "content": reply_content})
        _save_session(session_id, messages)

        # 用 DeepSeek 文本直接搜索（原 fipai tool_calls 路径已弃用）
        mutual_map = self._get_mutual_connections(profile) if profile else {}
        recommendations = self._direct_search(reply_content, profile, mutual_map)

        return Response({
            'code': 0,
            'data': {
                'session_id': session_id,
                'content': reply_content,
                'channel': channel,
                'recommendations': recommendations,
                'tool_calls': [],
                'tool_results': [],
            }
        })

    def _direct_search(self, text: str, profile=None, mutual_map=None) -> list:
        """
        Direct LLM fallback：当LLM没有调用工具时，解析文本中的关键词并直接搜索供需库
        """
        import re
        from supplies.models import Supply

        recommendations = []
        mutual_map = mutual_map or {}
        try:
            # 简单关键词提取：中文、字母数字组合，2-20字符的词
            keywords = re.findall(r'[\u4e00-\u9fa5a-zA-Z0-9]{2,20}', text)
            keywords = [k for k in keywords if len(k) >= 2][:5]

            if not keywords:
                return recommendations

            qs = Supply.objects.filter(status=1).select_related('profile')
            # 用第一个关键词搜索
            keyword = keywords[0]
            qs = qs.filter(title__icontains=keyword) | qs.filter(content__icontains=keyword)

            ai_reason_text = self._extract_reason_from_reply(text)

            for s in qs[:10]:
                author_name = s.profile.real_name if not s.is_anonymous else "匿名用户"
                item_uuid = str(s.uuid)
                mutual_conns = mutual_map.get(item_uuid, [])
                # 关键词匹配的基础分（非随机，稳定 0.65）
                match_score = 0.65
                recommendations.append({
                    'uuid': item_uuid,
                    'title': s.title,
                    'supply_type': "supply" if s.supply_type == 1 else "demand",
                    'author_name': author_name,
                    'city': s.profile.city or '',
                    'tags': [],
                    'ai_reason': ai_reason_text or f'关键词"{keyword}"匹配',
                    'match_score': int(match_score * 100),
                    'mutual_connections': mutual_conns,
                })

        except Exception as e:
            logger.warning(f"[supply-matches] direct search error: {e}")

        return recommendations

    def _extract_reason_from_reply(self, text: str) -> str:
        # 从 DeepSeek 回复中提取推荐理由；没有则返回空（由调用方兜底）
        if not text:
            return ''
        # 简单提取：取第一段非空文本，截断到 100 字
        lines = [ln.strip() for ln in text.split('\n') if ln.strip()]
        if lines:
            return lines[0][:100]
        return text[:100]

    def _get_mutual_connections(self, profile) -> dict:
        return _get_mutual_connections(profile)

    def _calc_match_score(self, item: dict, profile) -> float:
        return _calc_match_score(item, profile)


class AIChatProxyV2View(APIView):
    """
    POST /api/v1/ai/chat-v2/ — AI对话V2代理
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_message = request.data.get('message', '')
        if not user_message:
            return Response({'code': 2002, 'message': 'message不能为空'}, status=status.HTTP_400_BAD_REQUEST)

        session_id = request.data.get('session_id', '')
        channel_hint = request.data.get('channel_hint', 'auto')

        # 生成或验证session_id
        if not session_id:
            session_id = str(uuid.uuid4())

        # 构建用户上下文（仅当前用户，防止 IDOR 枚举他人 PII）
        user_context = ""
        try:
            from profiles.models import Profile, ProfileTag
            profile = Profile.objects.get(user=request.user)
            my_tags = list(ProfileTag.objects.filter(profile=profile, tag_type=1).select_related('tag')[:5])
            tag_context = '、'.join(t.tag.name for t in my_tags) if my_tags else '暂无标签'
            user_context = (
                f'\n\n[用户背景] 姓名：{profile.real_name}，'
                f'公司：{profile.company}，职位：{profile.position}，'
                f'行业：{profile.industry}，城市：{profile.city}，'
                f'学校：{profile.education_school}，'
                f'标签：{tag_context}。'
            )
        except Exception as e:
            logger.warning(f"[chat-v2] load profile error: {e}")

        # 注入用户消息（带上下文）
        current_user_msg = user_message + user_context

        # 加载历史消息
        history = _load_session(session_id)

        # 构建完整的 messages 数组
        messages = []
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": current_user_msg})

        # 直接调 DeepSeek（替代 fipai.cn，2026-08-24）
        ok, reply_content = _call_deepseek(messages, temperature=0.7, max_tokens=1500, timeout=60)
        if not ok:
            return Response({'code': 5001, 'message': reply_content}, status=502)
        tool_calls = []

        # 更新会话历史：user消息 + assistant回复
        messages.append({"role": "assistant", "content": reply_content})
        _save_session(session_id, messages)

        result_data = {
            'content': reply_content,
            'channel': 'deepseek',
            'metadata': {},
            'session_id': session_id,
            'tool_calls': tool_calls,
        }

        return Response({'code': 0, 'data': result_data})


# ===== AI引导发布API =====

class AIActivityRecommendView(APIView):
    """
    GET /api/v1/ai/activity-recommend/ — AI活动推荐

    返回结构化的单个活动对象（带 AI 匹配理由），供前端 AI 精选卡片直接渲染。
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        import logging
        logger = logging.getLogger()

        user_context = ""
        try:
            from profiles.models import Profile, ProfileTag
            # 仅当前用户，防止 IDOR 枚举他人 PII
            profile = Profile.objects.get(user=request.user)

            my_tags = list(
                ProfileTag.objects.filter(profile=profile, tag_type=1)
                .select_related('tag')[:10]
            )
            tag_context = '、'.join(t.tag.name for t in my_tags) if my_tags else '暂无标签'
            user_context = (
                f"用户名：{profile.real_name}，"
                f"公司：{profile.company}，"
                f"职位：{profile.position}，"
                f"行业：{profile.industry}，"
                f"城市：{profile.city}，"
                f"标签：{tag_context}。"
            )
        except Exception as e:
            logger.warning(f"[activity-recommend] load profile error: {e}")
            user_context = "请推荐最相关的人文创业活动。"

        from activities.models import Activity
        from activities.serializers import ActivitySerializer

        # 取最近一个报名中的活动作为推荐主体
        activity = Activity.objects.filter(status=1, audit_status=1).order_by('-created_at').first()
        if not activity:
            return Response({'code': 0, 'data': None})

        # 用 DeepSeek 生成匹配理由（简短）
        prompt = (
            f"用户背景：{user_context}\n\n"
            f"活动：{activity.title}（{activity.location}）\n"
            f"活动介绍：{(activity.description or '')[:100]}\n\n"
            f"请用一句话（30字以内）说明这个活动为什么适合该用户，并给出0-100的匹配度。"
            f"只返回JSON：{{\"reason\": \"理由\", \"pct\": 85}}"
        )

        match_reason = ''
        match_pct = 70
        ok, reply_content = _call_deepseek(
            [{'role': 'user', 'content': prompt}],
            temperature=0.5,
            max_tokens=200,
            timeout=30,
        )
        if ok:
            import re as _re
            try:
                m = _re.search(r'\{.*\}', reply_content, _re.DOTALL)
                if m:
                    import json as _json
                    parsed = _json.loads(m.group())
                    match_reason = str(parsed.get('reason', ''))
                    match_pct = int(parsed.get('pct', 70))
            except Exception:
                pass

        # 组装前端期望的结构化字段
        item = ActivitySerializer(activity).data
        item['pct'] = match_pct
        item['match_reason'] = match_reason or '根据您的行业背景为您推荐'
        item['attendee_count'] = activity.current_attendees
        # 补 tags（JSONField 存 tag_id，转成 [{id, name}] 供前端渲染）
        try:
            from profiles.models import Tag
            tag_ids = [int(t) for t in (activity.tags or []) if str(t).isdigit()]
            tag_map = {t.id: t.name for t in Tag.objects.filter(id__in=tag_ids)}
            item['tags'] = [{'id': tid, 'name': tag_map.get(tid, '')} for tid in tag_ids if tag_map.get(tid)]
        except Exception:
            item['tags'] = []
        # 补 start_time_fmt（前端用），并保留 start_time 原始值
        if item.get('start_time'):
            item['start_time_fmt'] = str(item['start_time']).replace('T', ' ')[:16]
        else:
            item['start_time_fmt'] = ''

        return Response({'code': 0, 'data': item})


GUIDE_QUESTIONS = {
    0: {
        'question': '👋 你好！我是燃冰AI助手，可以帮你写一条高质量的供需发布。\n\n首先，告诉我你想发布的是：',
        'quick_replies': ['📤 我要供给（我有资源/服务可以分享）', '📥 我要需求（我在找资源/服务）'],
    },
    1: {
        'question': '好的！接下来：\n\n你想找什么？还是想提供什么？请简单描述一下你的核心需求或资源。例如：\n• "我想找企业服务方向的融资渠道"\n• "我可以提供企业级SaaS产品技术开发服务"\n• "我需要企业客户资源对接"\n\n一句话说明即可 😊',
        'quick_replies': ['我有融资渠道，想找企业服务项目', '我有技术开发能力，接外包', '我需要找企业客户渠道合作', '其他需求（请描述）'],
    },
    2: {
        'question': '明白了！最后一个问题：\n\n你希望谁能看到这条发布？比如：\n• 创业者、投资人\n• 企业服务从业者\n• 特定行业（教育、医疗等）\n• 校友网络\n\n这能帮我帮你写得更精准 ✨',
        'quick_replies': ['不限，公开给所有燃冰用户', '优先创业者/投资人', '企业服务/商务方向人士', '同行业校友'],
    },
}


def generate_suggestions(collected, user_profile=None):
    type_label = '供给' if collected.get('type') == 1 else '需求'
    topic = collected.get('title_hints', '')
    detail = collected.get('desc_hints', '')
    audience = collected.get('tag_hints', [])
    
    # Generate title
    title = topic if topic else (type_label + '资源合作')
    if len(title) > 50:
        title = title[:47] + '...'
    
    # Generate content
    content_parts = []
    if detail:
        content_parts.append(detail)
    if audience:
        content_parts.append(f"期望人群：{', '.join(audience)}")
    content = '\n'.join(content_parts) if content_parts else detail or ''
    
    # Suggest tags based on topic
    tag_map = {
        '融资': ['创业企业', '投资机构', '金融科技'],
        '技术': ['产品研发', '企业服务', '先进制造'],
        '客户': ['市场营销', '企业服务', '销售商务'],
        '品牌': ['市场营销', '设计创意', '消费零售'],
        '渠道': ['销售商务', '企业服务', '投资投行'],
        '人才': ['运营管理', '产品研发', '企业服务'],
    }
    suggested_tags = []
    for kw, tags in tag_map.items():
        if kw in topic or kw in detail:
            suggested_tags.extend(tags[:2])
    suggested_tags = list(dict.fromkeys(suggested_tags))[:3]
    
    return {
        'title': title,
        'content': content,
        'tags': suggested_tags,
        'type': collected.get('type'),
    }


@csrf_exempt
def ai_publish_guide(request):
    """POST /api/v1/ai/publish-guide/ - Guided AI publish conversation"""
    from django.http import JsonResponse
    
    try:
        body = json.loads(request.body)
        messages = body.get('messages', [])
        collected = body.get('collected', {})
    except:
        return JsonResponse({'code': 1, 'msg': 'invalid request'})
    
    # Count user messages
    user_msgs = [m for m in messages if m.get('role') == 'user']
    step = len(user_msgs)  # 0=type Q, 1=content Q, 2=audience Q
    
    # Update collected based on answers
    if len(user_msgs) >= 1:
        last_user = user_msgs[-1].get('content', '')
        if '供给' in last_user or '提供' in last_user or ('我有' in last_user and '需求' not in last_user):
            collected['type'] = 1
        else:
            collected['type'] = 2
    
    if len(user_msgs) >= 2:
        collected['title_hints'] = user_msgs[0].get('content', '') + ' ' + user_msgs[1].get('content', '')
    
    if len(user_msgs) >= 3:
        collected['tag_hints'] = [user_msgs[2].get('content', '')]
    
    # Check if complete
    if step >= 3:
        return JsonResponse({
            'code': 0,
            'msg': 'success',
            'data': {
                'is_complete': True,
                'step': 3,
                'collected': collected,
                'suggested': generate_suggestions(collected),
                'next_question': None,
            }
        })
    
    # Return next question
    q_data = GUIDE_QUESTIONS.get(step, GUIDE_QUESTIONS[0])
    return JsonResponse({
        'code': 0,
        'msg': 'success',
        'data': {
            'is_complete': False,
            'step': step,
            'collected': collected,
            'next_question': q_data['question'],
            'quick_replies': q_data.get('quick_replies'),
        }
    })
