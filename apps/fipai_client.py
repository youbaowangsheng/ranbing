"""
FIPAI API 客户端封装
"""
import httpx
from django.conf import settings


class FIPAIAPIClient:
    """燃冰调用FIPAI API的客户端"""

    def __init__(self):
        self.base_url = settings.FIPAI_BASE_URL
        self.api_key = settings.FIPAI_API_KEY
        self.timeout = 30.0

    def _get_headers(self):
        headers = {'Content-Type': 'application/json'}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        return headers

    def get_agents(self, params=None):
        """GET /api/agents/ - 获取Agent列表"""
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(
                f'{self.base_url}/api/agents/',
                headers=self._get_headers(),
                params=params or {}
            )
            response.raise_for_status()
            return response.json()

    def get_agent(self, agent_id):
        """GET /api/agents/{id}/ - 获取单个Agent"""
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(
                f'{self.base_url}/api/agents/{agent_id}/',
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()

    def create_agent(self, data):
        """POST /api/agents/ - 创建Agent"""
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f'{self.base_url}/api/agents/',
                headers=self._get_headers(),
                json=data
            )
            response.raise_for_status()
            return response.json()

    def update_agent(self, agent_id, data):
        """PUT /api/agents/{id}/ - 更新Agent"""
        with httpx.Client(timeout=self.timeout) as client:
            response = client.put(
                f'{self.base_url}/api/agents/{agent_id}/',
                headers=self._get_headers(),
                json=data
            )
            response.raise_for_status()
            return response.json()

    def delete_agent(self, agent_id):
        """DELETE /api/agents/{id}/ - 删除Agent"""
        with httpx.Client(timeout=self.timeout) as client:
            response = client.delete(
                f'{self.base_url}/api/agents/{agent_id}/',
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()


# 单例
_fipai_client = None

def get_fipai_client():
    global _fipai_client
    if _fipai_client is None:
        _fipai_client = FIPAIAPIClient()
    return _fipai_client