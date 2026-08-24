"""
Profile 上下文构建器 - 带 Redis 缓存

解决的问题：
- 之前每个 AI 视图都自己查 Profile + ProfileTag
- 每次都要 2~3 次 DB 查询，构成 N+1

优化后：
- 一次构建，缓存 5 分钟
- 同一用户 5 分钟内只查一次 DB

缓存 key 设计：
- ai:profile:{user_id} - 用户级（适合登录用户）
- ai:profile:uuid:{uuid} - profile_uuid 级（适合公开/匿名场景）
"""
import json
import logging
import threading
from typing import Optional

from django.conf import settings

logger = logging.getLogger(__name__)

CACHE_TTL = 300  # 5 分钟
_lock = threading.Lock()


def _get_redis():
    """获取 Redis 客户端（懒加载）"""
    if not hasattr(_get_redis, '_client'):
        try:
            import redis
            _get_redis._client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            _get_redis._client.ping()
        except Exception:
            _get_redis._client = None
    return _get_redis._client


def build_profile_context(user=None, profile_uuid=None, tag_limit=10):
    """
    构造 AI 用的 profile 上下文 dict（带 Redis 缓存）：
    {
        'real_name': '...',
        'company': '...',
        'position': '...',
        'industry': '...',
        'city': '...',
        'education_school': '...',
        'tags': ['标签1', '标签2', ...],
        'tags_str': '标签1、标签2',  # 拼接好的字符串
        'profile_uuid': '...',
        'cert_level': N,
    }

    返回 None 表示没找到 profile
    """
    from profiles.models import Profile, ProfileTag
    from django.contrib.auth.models import AnonymousUser

    # 1. 决定缓存 key
    cache_key = None
    if user and not isinstance(user, AnonymousUser) and getattr(user, 'id', None):
        cache_key = f'ai:profile:user:{user.id}'
    elif profile_uuid:
        cache_key = f'ai:profile:uuid:{profile_uuid}'

    # 2. 查缓存
    r = _get_redis()
    if cache_key and r:
        try:
            cached = r.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"[profile-ctx] cache read fail: {e}")

    # 3. 查 DB
    profile = None
    try:
        if profile_uuid:
            profile = Profile.objects.get(uuid=profile_uuid)
        elif user and not isinstance(user, AnonymousUser):
            profile = Profile.objects.get(user=user)
        else:
            return None
    except Profile.DoesNotExist:
        return None

    # 取 tag 名
    tag_names = list(profile.profile_tags
                     .select_related('tag')
                     .values_list('tag__name', flat=True)[:tag_limit])

    ctx = {
        'real_name': profile.real_name or '',
        'company': profile.company or '',
        'position': profile.position or '',
        'industry': profile.industry or '',
        'city': profile.city or '',
        'education_school': profile.education_school or '',
        'cert_level': profile.cert_level or 0,
        'tags': tag_names,
        'tags_str': '、'.join(tag_names) if tag_names else '暂无标签',
        'profile_uuid': str(profile.uuid),
    }

    # 4. 写缓存
    if cache_key and r:
        try:
            r.setex(cache_key, CACHE_TTL, json.dumps(ctx, ensure_ascii=False))
        except Exception as e:
            logger.warning(f"[profile-ctx] cache write fail: {e}")

    return ctx


def build_user_context_text(ctx: dict) -> str:
    """从 ctx dict 生成 LLM 可读的 user 文本片段"""
    if not ctx:
        return ''
    return (
        f'姓名：{ctx["real_name"]}，'
        f'公司：{ctx["company"]}，职位：{ctx["position"]}，'
        f'行业：{ctx["industry"]}，城市：{ctx["city"]}，'
        f'标签：{ctx["tags_str"]}。'
    )


def invalidate_profile_cache(user_id=None, profile_uuid=None):
    """主动失效（用户修改资料后调用）"""
    r = _get_redis()
    if not r:
        return
    try:
        if user_id:
            r.delete(f'ai:profile:user:{user_id}')
        if profile_uuid:
            r.delete(f'ai:profile:uuid:{profile_uuid}')
    except Exception:
        pass