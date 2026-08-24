"""
AI Gateway - 统一 LLM 调用入口

全项目 AI 调用必须经过这里：
- 业务层不准直接 httpx 调用 DeepSeek / FIPAI
- 改 API key / 改 URL / 加 retry / 加埋点，只改这一处
- 提供 chat / batch_chat / embedding 三个方法

特性：
- 单次 + 批量 chat
- 成本埋点（Redis 日累计）
- 用户级速率限制
- trace_id 全链路追踪
- mock 兜底（无 API key 时）
"""
import json
import time
import uuid
import logging
from typing import List, Dict, Any, Optional
from django.conf import settings
import httpx
import redis

logger = logging.getLogger(__name__)

# ── 成本表（元 / 1K tokens）────────────────────────────────
COST_PER_1K_TOKENS = {
    'deepseek-chat': 0.0014,
    'text-embedding-3-small': 0.0001,
}

# 用户速率限制（次/分钟）
USER_RATE_LIMIT = 20


class AICallBudgetExceeded(Exception):
    """用户/全局配额耗尽"""
    pass


class AIGateway:
    """统一 LLM 客户端，单例使用"""

    def __init__(self):
        self.api_key = settings.DEEPSEEK_API_KEY
        self.model = settings.DEEPSEEK_MODEL
        self.fipai_url = getattr(settings, 'FIPAI_GATEWAY_URL', 'https://fipai.cn/api/v1/chat/')
        self.timeout = 30
        self._redis = None

    @property
    def redis(self):
        if self._redis is None:
            try:
                self._redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
                self._redis.ping()
            except Exception:
                self._redis = None
        return self._redis

    # ── 公共方法 ────────────────────────────────────────
    def chat(self, messages, *, prompt_id=None, user_id=None,
             temperature=0.7, max_tokens=1000, tools=None,
             channel_hint=None, use_fipai=False):
        """
        单次 chat 调用
        prompt_id: 用于追踪是哪个 prompt 触发的（埋点/限流）
        user_id: 用于按用户限流
        use_fipai: True 时走 FIPAI 中台（支持 tool_calls）
        """
        trace_id = str(uuid.uuid4())[:8]
        self._check_rate_limit(user_id)

        if use_fipai:
            return self._chat_via_fipai(
                messages, tools=tools, channel_hint=channel_hint,
                trace_id=trace_id, prompt_id=prompt_id,
            )
        return self._chat_direct(
            messages, temperature=temperature, max_tokens=max_tokens,
            trace_id=trace_id, prompt_id=prompt_id,
        )

    def batch_chat(self, batch_messages: List[List[Dict]], *,
                   prompt_id=None, user_id=None, channel_hint='batch'):
        """
        同步批量调用：用于 AI Match 等场景，避免 N 次同步
        内部用 asyncio.run 包裹，只在同步视图里用
        """
        import asyncio
        trace_id = str(uuid.uuid4())[:8]
        self._check_rate_limit(user_id)
        return asyncio.run(self._batch_chat_async(
            batch_messages, channel_hint=channel_hint,
            trace_id=trace_id, prompt_id=prompt_id,
        ))

    async def abatch_chat(self, batch_messages: List[List[Dict]], *,
                          prompt_id=None, user_id=None, channel_hint='batch'):
        """
        异步批量调用：在 DRF async view 里用，不会触发 RuntimeError
        """
        trace_id = str(uuid.uuid4())[:8]
        self._check_rate_limit(user_id)
        return await self._batch_chat_async(
            batch_messages, channel_hint=channel_hint,
            trace_id=trace_id, prompt_id=prompt_id,
        )

    def embedding(self, text, *, prompt_id=None, user_id=None):
        """单条 embedding 调用"""
        trace_id = str(uuid.uuid4())[:8]
        self._check_rate_limit(user_id)
        return self._embedding_direct(text, trace_id=trace_id, prompt_id=prompt_id)

    # ── 内部实现 ────────────────────────────────────────
    def _chat_direct(self, messages, *, temperature, max_tokens,
                     trace_id, prompt_id):
        """直连 DeepSeek"""
        if not self.api_key:
            return self._mock_chat(messages)

        payload = {
            'model': self.model,
            'messages': messages,
            'temperature': temperature,
            'max_tokens': max_tokens,
        }
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(
                    'https://api.deepseek.com/chat/completions',
                    json=payload,
                    headers={'Authorization': f'Bearer {self.api_key}'},
                )
                resp.raise_for_status()
                data = resp.json()
                self._track_cost(data, prompt_id, trace_id)
                return data['choices'][0]['message']['content']
        except httpx.TimeoutException:
            logger.warning(f"[ai-gw] timeout trace={trace_id}")
            raise
        except Exception as e:
            logger.exception(f"[ai-gw] error trace={trace_id}: {e}")
            raise

    async def _batch_chat_async(self, batch_messages, *,
                                channel_hint, trace_id, prompt_id):
        """批量异步调用"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            tasks = [
                self._chat_via_fipai_async(
                    client, msgs, channel_hint=channel_hint,
                    trace_id=f"{trace_id}-{i}", prompt_id=prompt_id,
                )
                for i, msgs in enumerate(batch_messages)
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            # 异常转 None，保持顺序与输入一致
            return [r if not isinstance(r, Exception) else None for r in results]

    def _chat_via_fipai(self, messages, *, tools, channel_hint,
                        trace_id, prompt_id=None):
        """同步走 FIPAI"""
        payload = {
            'message': messages[-1]['content'] if messages else '',
            'messages': messages,
            'tools': tools or [],
            'channel_hint': channel_hint or 'single_agent',
        }
        try:
            with httpx.Client(timeout=60) as client:
                resp = client.post(
                    self.fipai_url, json=payload,
                    headers={'Content-Type': 'application/json'},
                )
                resp.raise_for_status()
                data = resp.json()
                logger.info(
                    f"[ai-gw] fipai trace={trace_id} channel={data.get('channel')}"
                )
                return data
        except Exception as e:
            logger.exception(f"[ai-gw] fipai error trace={trace_id}: {e}")
            raise

    async def _chat_via_fipai_async(self, client, messages, *,
                                    channel_hint, trace_id, prompt_id):
        """异步走 FIPAI（batch 用）"""
        payload = {
            'message': messages[-1]['content'] if messages else '',
            'messages': messages,
            'tools': [],
            'channel_hint': channel_hint or 'batch',
        }
        try:
            resp = await client.post(
                self.fipai_url, json=payload,
                headers={'Content-Type': 'application/json'},
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.warning(f"[ai-gw] batch fipai error trace={trace_id}: {e}")
            return None

    def _embedding_direct(self, text, *, trace_id, prompt_id):
        """直连 DeepSeek embedding"""
        if not self.api_key:
            return self._mock_embedding()
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(
                    'https://api.deepseek.com/embeddings',
                    json={'model': 'text-embedding-3-small', 'input': text},
                    headers={'Authorization': f'Bearer {self.api_key}'},
                )
                resp.raise_for_status()
                data = resp.json()
                # 埋点
                self._track_embedding_cost(data, prompt_id, trace_id)
                return data['data'][0]['embedding']
        except Exception as e:
            logger.exception(f"[ai-gw] embedding error trace={trace_id}: {e}")
            return self._mock_embedding()

    # ── 速率限制 / 成本追踪 ─────────────────────────────
    def _check_rate_limit(self, user_id):
        """按用户限流：每用户每分钟最多 USER_RATE_LIMIT 次"""
        if not user_id or not self.redis:
            return
        key = f'ai:rate:{user_id}'
        try:
            count = self.redis.incr(key)
            if count == 1:
                self.redis.expire(key, 60)
            if count > USER_RATE_LIMIT:
                raise AICallBudgetExceeded(
                    f'AI 调用过于频繁（{USER_RATE_LIMIT}次/分钟），请稍后再试'
                )
        except redis.RedisError:
            pass

    def _track_cost(self, response, prompt_id, trace_id):
        """记录 chat 成本"""
        try:
            usage = response.get('usage', {}) if isinstance(response, dict) else {}
            total_tokens = usage.get('total_tokens', 0)
            cost = (total_tokens / 1000) * COST_PER_1K_TOKENS.get(self.model, 0.001)
            logger.info(
                f"[ai-cost] trace={trace_id} prompt={prompt_id} "
                f"tokens={total_tokens} cost={cost:.4f}元"
            )
            if self.redis and total_tokens > 0:
                today = time.strftime('%Y-%m-%d')
                pipe = self.redis.pipeline()
                pipe.hincrby(f'ai:cost:{today}', 'tokens', total_tokens)
                pipe.hincrbyfloat(f'ai:cost:{today}', 'cost', cost)
                pipe.sadd(f'ai:prompts:{today}', prompt_id or 'unknown')
                pipe.execute()
        except Exception:
            pass

    def _track_embedding_cost(self, response, prompt_id, trace_id):
        """记录 embedding 成本"""
        try:
            usage = response.get('usage', {}) if isinstance(response, dict) else {}
            total_tokens = usage.get('total_tokens', 0)
            cost = (total_tokens / 1000) * COST_PER_1K_TOKENS.get(
                'text-embedding-3-small', 0.0001
            )
            logger.info(
                f"[ai-embed-cost] trace={trace_id} prompt={prompt_id} "
                f"tokens={total_tokens} cost={cost:.4f}元"
            )
            if self.redis and total_tokens > 0:
                today = time.strftime('%Y-%m-%d')
                pipe = self.redis.pipeline()
                pipe.hincrby(f'ai:cost:{today}', 'embed_tokens', total_tokens)
                pipe.hincrbyfloat(f'ai:cost:{today}', 'embed_cost', cost)
                pipe.execute()
        except Exception:
            pass

    # ── Mock 兜底 ───────────────────────────────────────
    def _mock_chat(self, messages):
        last = messages[-1]['content'] if messages else ''
        return f'已收到您的请求"{"".join(last.split()[-5:])}"，AI 正在配置中。'

    def _mock_embedding(self):
        import random
        return [random.uniform(-1, 1) for _ in range(1536)]


# 单例
gateway = AIGateway()