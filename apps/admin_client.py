"""
燃冰后台 Admin 客户端 - 调用 backend API 进行审核操作
"""
import os
import httpx
from typing import Optional


# backend API 基础 URL
RANBING_BACKEND_URL = os.environ.get('RANBING_BACKEND_URL', 'http://localhost:8003')


class RanbingAdminClient:
    """调用 backend 审核 API 的客户端"""

    def __init__(self):
        self.client = httpx.Client(
            base_url=RANBING_BACKEND_URL,
            timeout=30.0,
            headers={'Content-Type': 'application/json'}
        )

    def _request(self, method: str, path: str, **kwargs):
        """发起请求"""
        try:
            resp = self.client.request(method, path, **kwargs)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"[RanbingAdminClient] {method} {path} error: {e}")
            return {'code': 500, 'message': str(e)}

    # ============ 活动审核 ============

    def get_activities_pending(self, page: int = 1, page_size: int = 20):
        """获取待审核活动"""
        return self._request('GET', '/api/v1/activities/pending/', params={'page': page, 'page_size': page_size})

    def get_activities_all(self, page: int = 1, page_size: int = 20):
        """获取所有活动（含审核状态）"""
        return self._request('GET', '/api/v1/activities/', params={'page': page, 'page_size': page_size})

    def approve_activity(self, uuid: str):
        """审核通过活动"""
        return self._request('POST', f'/api/v1/activities/{uuid}/approve/')

    def reject_activity(self, uuid: str, comment: str = ''):
        """审核拒绝活动"""
        return self._request('POST', f'/api/v1/activities/{uuid}/reject/', json={'comment': comment})

    # ============ 供需审核 ============

    def get_supplies_pending(self, page: int = 1, page_size: int = 20):
        """获取待审核供需"""
        return self._request('GET', '/api/v1/supplies/pending/', params={'page': page, 'page_size': page_size})

    def get_supplies_all(self, page: int = 1, page_size: int = 20):
        """获取所有供需"""
        return self._request('GET', '/api/v1/supplies/', params={'page': page, 'page_size': page_size})

    def approve_supply(self, uuid: str):
        """审核通过供需"""
        return self._request('POST', f'/api/v1/supplies/{uuid}/approve/')

    def reject_supply(self, uuid: str):
        """审核拒绝供需"""
        return self._request('POST', f'/api/v1/supplies/{uuid}/reject/')

    # ============ 社群审核 ============

    def get_communities_pending(self, page: int = 1, page_size: int = 20):
        """获取待审核社群"""
        return self._request('GET', '/api/v1/communities/pending/', params={'page': page, 'page_size': page_size})

    def approve_community(self, uuid: str):
        """审核通过社群"""
        return self._request('POST', f'/api/v1/communities/{uuid}/approve/')

    def reject_community(self, uuid: str):
        """审核拒绝社群"""
        return self._request('POST', f'/api/v1/communities/{uuid}/reject/')

    # ============ 社群消息审核 ============

    def get_messages_pending(self, page: int = 1, page_size: int = 20):
        """获取待审核消息"""
        return self._request('GET', '/api/v1/communities/pending_messages/', params={'page': page, 'page_size': page_size})

    def get_communities_pending(self, page: int = 1, page_size: int = 20):
        """获取待审核社群"""
        return self._request('GET', '/api/v1/communities/pending/', params={'page': page, 'page_size': page_size})

    def get_community_messages(self, community_uuid: str, page: int = 1, page_size: int = 20):
        """获取社群消息列表"""
        return self._request('GET', f'/api/v1/communities/{community_uuid}/messages/', params={'page': page, 'page_size': page_size})

    def audit_message(self, community_uuid: str, msg_id: int, action: str):
        """
        审核消息
        action: 'approve' 或 'reject'
        """
        return self._request('POST', f'/api/v1/communities/{community_uuid}/messages/{msg_id}/audit/', json={'action': action})

    def close(self):
        self.client.close()


# 全局单例
_admin_client: Optional[RanbingAdminClient] = None


def get_admin_client() -> RanbingAdminClient:
    global _admin_client
    if _admin_client is None:
        _admin_client = RanbingAdminClient()
    return _admin_client