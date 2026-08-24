"""
本 app 暴露给 AI 的工具 - 活动搜索
"""

SCHEMA = {
    "type": "function",
    "function": {
        "name": "search_activities",
        "description": (
            "搜索社交活动，支持按关键词、日期范围过滤。"
            "默认返回报名中或进行中的活动。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "keyword": {
                    "type": "string",
                    "description": "关键词，匹配活动标题和描述",
                },
                "start_after": {
                    "type": "string",
                    "description": "开始时间下限，ISO 格式如 2025-01-01",
                },
                "start_before": {
                    "type": "string",
                    "description": "开始时间上限，ISO 格式如 2025-12-31",
                },
                "activity_type": {
                    "type": "integer",
                    "description": "活动类型（1=沙龙 2=路演 3=培训班 4=社交聚会 5=线上讲座）",
                },
                "city": {
                    "type": "string",
                    "description": "活动所在城市",
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


def handler(keyword=None, start_after=None, start_before=None,
            activity_type=None, city=None, limit=10, **kwargs):
    """执行 search_activities"""
    from datetime import datetime
    from django.db.models import Q
    from .models import Activity

    limit = min(int(limit), 50)
    qs = Activity.objects.filter(status__in=[1, 2]).select_related('organizer__user')

    if keyword:
        qs = qs.filter(
            Q(title__icontains=keyword) | Q(description__icontains=keyword)
        )

    if start_after:
        try:
            after_dt = datetime.fromisoformat(start_after)
            qs = qs.filter(start_time__gte=after_dt)
        except ValueError:
            pass

    if start_before:
        try:
            before_dt = datetime.fromisoformat(start_before)
            qs = qs.filter(start_time__lte=before_dt)
        except ValueError:
            pass

    if activity_type is not None:
        qs = qs.filter(activity_type=int(activity_type))

    if city:
        qs = qs.filter(city__icontains=city)

    results = list(qs.order_by('-start_time')[:limit])

    items = []
    for a in results:
        organizer = a.organizer
        items.append({
            "uuid": str(a.uuid),
            "title": a.title,
            "description": (a.description or "")[:200],
            "activity_type": a.activity_type,
            "location": a.location,
            "city": a.location,  # Activity 用 location 字段，没有独立 city
            "start_time": a.start_time.isoformat() if a.start_time else None,
            "fee": str(a.fee) if a.fee else None,
            "enrollment_mode": a.enrollment_mode,
            "organizer_name": organizer.real_name if organizer else "",
            "current_attendees": a.current_attendees,
            "max_attendees": a.max_attendees,
        })

    return {"items": items, "total": len(items)}