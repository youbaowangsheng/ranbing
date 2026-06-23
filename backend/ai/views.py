"""AI相关API视图"""
import json
import uuid
import redis
import logging
import asyncio

import httpx
from django.conf import settings
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import AllowAny, IsAuthenticated

from .services.intent import (
    recognize_intent, extract_tags, generate_match_reason,
    generate_introduction_script, generate_followup_script
)
from .tools import TOOL_SCHEMAS, execute_tool

logger = logging.getLogger(__name__)


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
    permission_classes = [AllowAny]

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

    async def get(self, request):
        user_message = request.query_params.get('message', '')
        session_id = request.query_params.get('session_id', '')
        profile_uuid = request.query_params.get('profile_uuid', '')

        # 生成或验证session_id
        if not session_id:
            session_id = str(uuid.uuid4())

        # 加载用户profile（优先用profile_uuid，否则用request.user）
        user_context = ""
        profile = None
        try:
            from profiles.models import Profile, ProfileTag
            if profile_uuid:
                profile = Profile.objects.get(uuid=profile_uuid)
            else:
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

        # 代理请求到FIPAI
        fipai_url = 'https://fipai.cn/api/v1/chat/'
        fipai_payload = {
            'message': current_user_msg,
            'messages': messages,
            'tools': TOOL_SCHEMAS,
            'channel_hint': 'single_agent',
        }

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    fipai_url,
                    json=fipai_payload,
                    headers={'Content-Type': 'application/json'}
                )
                resp.raise_for_status()
                data = resp.json()

            reply_content = data.get('content', '') or data.get('reply', '')
            tool_calls = data.get('tool_calls', [])
            channel = data.get('channel', 'fipai')

            # 更新会话历史
            messages.append({"role": "assistant", "content": reply_content})
            _save_session(session_id, messages)

            recommendations = []
            tool_results = []

            # 尝试从FIPAI回复中提取AI理由
            ai_reason_text = self._extract_reason_from_reply(reply_content)

            # 如果有profile，查询共同连接
            mutual_map = {}
            if profile:
                mutual_map = self._get_mutual_connections(profile)

            # 如果FIPAI返回了tool_calls，执行它们
            if tool_calls:
                for tc in tool_calls:
                    result = execute_tool(tc)
                    tool_results.append(result)
                    # 尝试从结果中提取供需推荐
                    res = result.get('result', {})
                    if 'items' in res:
                        for item in res['items']:
                            item_uuid = item.get('uuid', '')
                            # 计算匹配度（标签重叠数 + 基础分）
                            match_score = self._calc_match_score(item, profile)
                            # 获取共同连接
                            mutual_conns = mutual_map.get(item_uuid, [])
                            recommendations.append({
                                'uuid': item_uuid,
                                'title': item.get('title', ''),
                                'supply_type': item.get('supply_type', ''),
                                'author_name': item.get('author_name', ''),
                                'city': item.get('city', ''),
                                'tags': item.get('tags', []),
                                'ai_reason': ai_reason_text or item.get('ai_reason', ''),
                                'match_score': int(match_score * 100),
                                'mutual_connections': mutual_conns,
                            })
            else:
                # Direct LLM fallback：解析文本关键词，直接搜索供需库
                recommendations = self._direct_search(reply_content, profile, mutual_map)

            return Response({
                'code': 0,
                'data': {
                    'session_id': session_id,
                    'content': reply_content,
                    'channel': channel,
                    'recommendations': recommendations,
                    'tool_calls': tool_calls,
                    'tool_results': tool_results,
                }
            })

        except httpx.TimeoutException:
            return Response({'code': 5001, 'message': 'AI服务响应超时，请稍后重试'}, status=504)
        except httpx.HTTPStatusError as e:
            return Response({'code': 5002, 'message': f'AI服务错误: {e.response.status_code}'}, status=502)
        except Exception as e:
            logger.exception(f"[supply-matches] unexpected error: {e}")
            return Response({'code': 5000, 'message': f'请求失败: {str(e)}'}, status=500)

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
                # 简单匹配度：随机60-90
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
        return _extract_reason_from_reply(text)

    def _get_mutual_connections(self, profile) -> dict:
        return _get_mutual_connections(profile)

    def _calc_match_score(self, item: dict, profile) -> float:
        return _calc_match_score(item, profile)


class AIChatProxyV2View(APIView):
    """
    POST /api/v1/ai/chat-v2/ — AI对话V2代理
    """
    permission_classes = [IsAuthenticated]

    async def post(self, request):
        user_message = request.data.get('message', '')
        if not user_message:
            return Response({'code': 2002, 'message': 'message不能为空'}, status=status.HTTP_400_BAD_REQUEST)

        session_id = request.data.get('session_id', '')
        channel_hint = request.data.get('channel_hint', 'auto')
        user_profile_uuid = request.data.get('user_profile_uuid')

        # 生成或验证session_id
        if not session_id:
            session_id = str(uuid.uuid4())

        # 构建用户上下文（可选）
        user_context = ""
        if user_profile_uuid:
            try:
                from profiles.models import Profile, ProfileTag
                profile = Profile.objects.get(uuid=user_profile_uuid)
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

        # 代理请求到FIPAI
        fipai_url = 'https://fipai.cn/api/v1/chat/'
        fipai_payload = {
            'message': current_user_msg,
            'messages': messages,
            'tools': TOOL_SCHEMAS,
            'channel_hint': channel_hint,
        }

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    fipai_url,
                    json=fipai_payload,
                    headers={'Content-Type': 'application/json'}
                )
                resp.raise_for_status()
                data = resp.json()

            # 提取响应内容
            reply_content = data.get('content', '') or data.get('reply', '')
            tool_calls = data.get('tool_calls', [])

            # 更新会话历史：user消息 + assistant回复
            messages.append({"role": "assistant", "content": reply_content})
            _save_session(session_id, messages)

            result_data = {
                'content': reply_content,
                'channel': data.get('channel', 'fipai'),
                'metadata': data.get('metadata', {}),
                'session_id': session_id,
                'tool_calls': tool_calls,
            }

            # 如果FIPAI返回了tool_calls，在本地执行它们
            if tool_calls:
                tool_results = []
                # 查询共同连接（用于匹配度增强）
                mutual_map = {}
                profile_for_score = None
                if user_profile_uuid:
                    try:
                        from profiles.models import Profile
                        profile_for_score = Profile.objects.get(uuid=user_profile_uuid)
                        # 用AISupplyMatchesView的逻辑查询共同连接
                        mutual_map = self._get_mutual_connections(profile_for_score)
                    except Exception:
                        pass

                for tc in tool_calls:
                    result = execute_tool(tc)
                    tool_results.append(result)
                    # 补充 match_score + mutual_connections
                    res = result.get('result', {})
                    if 'items' in res:
                        for item in res['items']:
                            score = self._calc_match_score(item, profile_for_score)
                            item['match_score'] = int(score * 100)
                            mutual = mutual_map.get(item.get('uuid', ''), [])
                            item['mutual_connections'] = mutual
                result_data['tool_results'] = tool_results

            return Response({'code': 0, 'data': result_data})

        except httpx.TimeoutException:
            return Response({'code': 5001, 'message': 'AI服务响应超时，请稍后重试'}, status=504)
        except httpx.HTTPStatusError as e:
            return Response({'code': 5002, 'message': f'AI服务错误: {e.response.status_code}'}, status=502)
        except Exception as e:
            logger.exception(f"[chat-v2] unexpected error: {e}")
            return Response({'code': 5000, 'message': f'请求失败: {str(e)}'}, status=500)


# ===== AI引导发布API =====

class AIActivityRecommendView(APIView):
    """
    GET /api/v1/ai/activity-recommend/ — AI活动推荐
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        import logging
        logger = logging.getLogger()
        profile_uuid = request.query_params.get('profile_uuid', '')

        user_context = ""
        try:
            from profiles.models import Profile, ProfileTag
            if profile_uuid:
                profile = Profile.objects.get(uuid=profile_uuid)
            else:
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
        recent_activities = Activity.objects.filter(status=1).order_by('-created_at')[:5]
        activity_context = "\n".join([
            f"- {a.title}（{a.city}）"
            for a in recent_activities
        ]) if recent_activities else "暂无活动"

        prompt = (
            f"根据用户背景，推荐最相关的人文创业活动。\n\n"
            f"用户信息：\n{user_context}\n\n"
            f"最近活动：\n{activity_context}\n\n"
            f"请只推荐最相关的2-3个活动，说明推荐理由。"
        )

        fipai_url = 'https://fipai.cn/api/v1/chat/'
        fipai_payload = {
            'message': prompt,
            'messages': [{"role": "user", "content": prompt}],
            'tools': [],
            'channel_hint': 'single_agent',
        }

        try:
            resp = httpx.post(
                fipai_url,
                json=fipai_payload,
                headers={'Content-Type': 'application/json'},
                timeout=60
            )
            resp.raise_for_status()
            data = resp.json()

            reply_content = data.get('content', '') or data.get('reply', '')
            return Response({'code': 0, 'data': {'recommendation': reply_content}})
        except Exception as e:
            logger.error(f"[activity-recommend] error: {e}")
            return Response({'code': 1, 'message': str(e)}, status=500)


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


@login_required
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
