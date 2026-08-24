"""
本 app 暴露给 AI 的工具 - 社群搜索
"""
from django.db.models import Q

SCHEMA = {
    "type": "function",
    "function": {
        "name": "search_communities",
        "description": (
            "搜索社群（行业群/校友群/兴趣群等），"
            "支持按关键词、行业、城市过滤。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "keyword": {
                    "type": "string",
                    "description": "关键词，匹配社群名和简介",
                },
                "community_type": {
                    "type": "integer",
                    "description": "社群类型（1=行业 2=地域 3=校友 4=兴趣）",
                },
                "city": {
                    "type": "string",
                    "description": "所在城市",
                },
                "min_members": {
                    "type": "integer",
                    "description": "最少成员数",
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


def handler(keyword=None, community_type=None, city=None,
            min_members=None, limit=10, **kwargs):
    """执行 search_communities"""
    from .models import Community

    limit = min(int(limit), 50)
    qs = Community.objects.filter(status__in=[1, 2]).select_related('owner__user')

    if keyword:
        qs = qs.filter(
            Q(name__icontains=keyword) | Q(description__icontains=keyword)
        )
    if community_type is not None:
        qs = qs.filter(community_type=int(community_type))
    if city:
        qs = qs.filter(city__icontains=city)
    if min_members is not None:
        qs = qs.filter(member_count__gte=int(min_members))

    results = list(qs.order_by('-member_count')[:limit])

    items = []
    for c in results:
        owner = c.owner
        items.append({
            "uuid": str(c.uuid),
            "name": c.name,
            "description": (c.description or "")[:200],
            "community_type": c.community_type,
            "city": c.city,
            "member_count": c.member_count,
            "owner_name": owner.real_name if owner else "",
            "industry": getattr(c, 'industry', ''),
        })

    return {"items": items, "total": len(items)}