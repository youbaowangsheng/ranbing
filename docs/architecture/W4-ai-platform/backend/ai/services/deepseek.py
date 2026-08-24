"""
DeepSeek API 封装（兼容层）

⚠️ 弃用警告：新代码请直接使用 `ai.gateway.gateway`
   - chat  → gateway.chat(messages, ...)
   - embedding → gateway.embedding(text, ...)

旧 DeepSeekClient 保留只为兼容可能的旧 import（如有）。
"""
import warnings
from ..gateway import gateway as _gateway


class DeepSeekClient:
    """兼容层：转发到 gateway"""

    def __init__(self):
        warnings.warn(
            "DeepSeekClient 已弃用，请改用 ai.gateway.gateway",
            DeprecationWarning, stacklevel=2,
        )

    def chat(self, messages, temperature=0.7, max_tokens=1000):
        return _gateway.chat(
            messages, temperature=temperature, max_tokens=max_tokens,
            prompt_id='legacy_deepseek_client',
        )

    def embedding(self, text):
        return _gateway.embedding(text, prompt_id='legacy_deepseek_embed')


# 旧 _mock_chat 留给直接 import 的脚本
def _mock_chat(messages):
    last = messages[-1]['content'] if messages else ''
    if '找' in last or '投资' in last:
        return '我为您找到了一批相关资源，点击查看详情。'
    return '好的，我已经理解了您的需求，正在为您处理。'


def _mock_embedding():
    import random
    return [random.uniform(-1, 1) for _ in range(1536)]
