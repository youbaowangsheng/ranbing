"""
DeepSeek API 封装
"""
import json
import httpx
from django.conf import settings


class DeepSeekClient:
    BASE_URL = 'https://api.deepseek.com'

    def __init__(self):
        self.api_key = settings.DEEPSEEK_API_KEY
        self.model = settings.DEEPSEEK_MODEL

    def chat(self, messages, temperature=0.7, max_tokens=1000):
        """调用DeepSeek Chat API"""
        if not self.api_key:
            return self._mock_chat(messages)

        payload = {
            'model': self.model,
            'messages': messages,
            'temperature': temperature,
            'max_tokens': max_tokens,
        }
        try:
            with httpx.Client(timeout=30) as client:
                resp = client.post(
                    f'{self.BASE_URL}/chat/completions',
                    json=payload,
                    headers={'Authorization': f'Bearer {self.api_key}'}
                )
                resp.raise_for_status()
                data = resp.json()
                return data['choices'][0]['message']['content']
        except Exception as e:
            print(f'[DeepSeek Error] {e}')
            return self._mock_chat(messages)

    def embedding(self, text):
        """调用DeepSeek Embedding API"""
        if not self.api_key:
            return self._mock_embedding()

        payload = {
            'model': 'text-embedding-3-small',
            'input': text,
        }
        try:
            with httpx.Client(timeout=30) as client:
                resp = client.post(
                    f'{self.BASE_URL}/embeddings',
                    json=payload,
                    headers={'Authorization': f'Bearer {self.api_key}'}
                )
                resp.raise_for_status()
                data = resp.json()
                return data['data'][0]['embedding']
        except Exception as e:
            print(f'[DeepSeek Embedding Error] {e}')
            return self._mock_embedding()

    def _mock_chat(self, messages):
        """Mock响应"""
        last_msg = messages[-1]['content'] if messages else ''
        if '找' in last_msg or '投资' in last_msg:
            return '我为您找到了一批相关资源，点击查看详情。'
        return '好的，我已经理解了您的需求，正在为您处理。'

    def _mock_embedding(self):
        """Mock向量（1536维）"""
        import random
        return [random.uniform(-1, 1) for _ in range(1536)]
