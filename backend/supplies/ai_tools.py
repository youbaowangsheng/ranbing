"""
本 app 暴露给 AI 的工具

新工具规范：
1. 定义 SCHEMA（OpenAI Function Calling 格式）
2. 定义 handler(**kwargs) 执行函数
3. 可选 PERMISSIONS 声明权限要求

注册由 ai.registry.discover_tools() 自动完成。
"""
from django.db.models import Q

SCHEMA = {
    "type": "function",
    "function": {
        "name": "search_supplies",
        "description": (
            "搜索供需广场的资源供给或需求。"
            "支持按关键词（title/content）、tag_id 精确过滤、"
            "supply_type（supply=供给 / demand=需求）、limit 上限。"
            "返回每条供需的 uuid/title/content/author/city/tags 等。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "keyword": {
                    "type": "string",
                    "description": "搜索关键词，匹配标题和内容",
                },
                "tag_id": {
                    "type": "integer",
                    "description": "标签ID，精确过滤",
                },
                "supply_type": {
                    "type": "string",
                    "enum": ["supply", "demand"],
                    "description": "supply=供给(我有资源) / demand=需求(我找资源)",
                },
                "limit": {
                    "type": "integer",
                    "default": 10,
                    "description": "返回结果数量上限（最大50）",
                },
            },
        },
    },
}


def handler(keyword=None, tag_id=None, supply_type=None, limit=10, **kwargs):
    """
    执行 search_supplies：查询供需表
    """
    from .models import Supply
    from profiles.models import Tag

    limit = min(int(limit), 50)
    qs = Supply.objects.filter(status=1).select_related('profile__user')

    # supply_type: 1=供给, 2=需求
    if supply_type == 'supply':
        qs = qs.filter(supply_type=1)
    elif supply_type == 'demand':
        qs = qs.filter(supply_type=2)

    # 标签过滤（tags 是 JSONField，存 tag_id 列表）
    if tag_id:
        qs = qs.filter(tags__contains=[tag_id])

    # 关键词过滤
    if keyword:
        qs = qs.filter(
            Q(title__icontains=keyword) | Q(content__icontains=keyword)
        )

    results = list(qs.order_by('-created_at')[:limit])

    items = []
    for s in results:
        # tag_id 列表 → tag 名称
        tag_names = []
        if s.tags:
            tag_ids = [int(t) for t in s.tags if str(t).isdigit()]
            if tag_ids:
                tag_map = {t.id: t.name for t in Tag.objects.filter(id__in=tag_ids)}
                tag_names = [tag_map.get(tid, '') for tid in tag_ids if tag_map.get(tid)]

        profile = s.profile
        items.append({
            "uuid": str(s.uuid),
            "title": s.title,
            "content": (s.content or "")[:200],
            "supply_type": "supply" if s.supply_type == 1 else "demand",
            "author_name": (profile.real_name if not s.is_anonymous and profile
                            else "匿名用户"),
            "city": profile.city if profile else "",
            "tags": tag_names,
            "is_anonymous": s.is_anonymous,
            "match_count": s.match_count,
            "view_count": s.view_count,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        })

    return {"items": items, "total": len(items)}