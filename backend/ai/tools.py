"""
AI工具定义与执行函数 - search_supplies / search_profiles / search_activities
"""
import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 工具Schema定义（OpenAI兼容格式）
# ---------------------------------------------------------------------------

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "search_supplies",
            "description": "搜索供需广场的资源供给或需求，支持按关键词、标签、类型过滤",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "搜索关键词，匹配标题和内容"
                    },
                    "tag_id": {
                        "type": "integer",
                        "description": "标签ID，精确过滤"
                    },
                    "supply_type": {
                        "type": "string",
                        "enum": ["supply", "demand"],
                        "description": "供给(supply)或需求(demand)"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 10,
                        "description": "返回结果数量上限"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_profiles",
            "description": "搜索校友档案，支持按行业、职位、学校、城市等维度过滤",
            "parameters": {
                "type": "object",
                "properties": {
                    "industry": {
                        "type": "string",
                        "description": "行业，如：互联网、金融、医疗"
                    },
                    "position": {
                        "type": "string",
                        "description": "职位关键词"
                    },
                    "school": {
                        "type": "string",
                        "description": "毕业学校名称"
                    },
                    "city": {
                        "type": "string",
                        "description": "所在城市"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 10,
                        "description": "返回结果数量上限"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_activities",
            "description": "搜索社交活动，支持按关键词、日期范围过滤",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "搜索关键词，匹配活动标题和描述"
                    },
                    "start_after": {
                        "type": "string",
                        "description": "开始时间下限，ISO格式如 2025-01-01"
                    },
                    "start_before": {
                        "type": "string",
                        "description": "开始时间上限，ISO格式如 2025-12-31"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 10,
                        "description": "返回结果数量上限"
                    }
                }
            }
        }
    }
]


# ---------------------------------------------------------------------------
# 工具执行函数
# ---------------------------------------------------------------------------

def exec_search_supplies(
    keyword: Optional[str] = None,
    tag_id: Optional[int] = None,
    supply_type: Optional[str] = None,
    limit: int = 10,
    **kwargs
) -> Dict[str, Any]:
    """
    执行 search_supplies：查询供需表，支持关键词、标签ID、供给类型过滤
    """
    try:
        from supplies.models import Supply
        from profiles.models import Profile

        limit = min(int(limit), 50)
        qs = Supply.objects.filter(status=1).select_related('profile')

        # supply_type: 1=供给, 2=需求
        if supply_type == 'supply':
            qs = qs.filter(supply_type=1)
        elif supply_type == 'demand':
            qs = qs.filter(supply_type=2)

        # 标签过滤（tags是JSONField，存tag_id列表）
        if tag_id:
            qs = qs.filter(tags__contains=[tag_id])

        # 关键词过滤（title + content）
        if keyword:
            qs = (qs.filter(title__icontains=keyword) | qs.filter(content__icontains=keyword))

        results = list(qs[:limit])

        items = []
        for s in results:
            author_name = s.profile.real_name if not s.is_anonymous else "匿名用户"
            city = s.profile.city or ""

            # 解析 tag_id 列表 -> tag 名称列表
            tag_names = []
            if s.tags:
                tag_ids = [int(tid) for tid in s.tags if str(tid).isdigit()]
                if tag_ids:
                    from profiles.models import Tag
                    tag_map = {t.id: t.name for t in Tag.objects.filter(id__in=tag_ids)}
                    tag_names = [tag_map.get(tid, '') for tid in tag_ids if tag_map.get(tid)]

            items.append({
                "uuid": str(s.uuid),
                "title": s.title,
                "content": s.content[:200] if s.content else "",
                "supply_type": "supply" if s.supply_type == 1 else "demand",
                "author_name": author_name,
                "city": city,
                "tags": tag_names,
                "is_anonymous": s.is_anonymous,
                "match_count": s.match_count,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            })
        return {"items": items, "total": len(items)}
    except Exception as e:
        logger.exception(f"[tools] search_supplies error: {e}")
        return {"items": [], "total": 0, "error": str(e)}


def exec_search_profiles(
    industry: Optional[str] = None,
    position: Optional[str] = None,
    school: Optional[str] = None,
    city: Optional[str] = None,
    limit: int = 10,
    **kwargs
) -> Dict[str, Any]:
    """
    执行 search_profiles：查询校友档案表
    """
    try:
        from profiles.models import Profile

        limit = min(int(limit), 50)
        qs = Profile.objects.filter(cert_status=2)  # 已认证

        if industry:
            qs = qs.filter(industry__icontains=industry)
        if position:
            qs = qs.filter(position__icontains=position)
        if school:
            qs = qs.filter(education_school__icontains=school)
        if city:
            qs = qs.filter(city__icontains=city)

        results = list(qs.select_related('user')[:limit])

        items = []
        for p in results:
            items.append({
                "uuid": str(p.uuid),
                "real_name": p.real_name,
                "company": p.company,
                "position": p.position,
                "industry": p.industry,
                "city": p.city,
                "education_school": p.education_school,
                "education_year": p.education_year,
                "cert_level": p.cert_level,
                "avatar_url": getattr(p.user, 'avatar_url', '') if hasattr(p, 'user') else '',
            })
        return {"items": items, "total": len(items)}
    except Exception as e:
        logger.exception(f"[tools] search_profiles error: {e}")
        return {"items": [], "total": 0, "error": str(e)}


def exec_search_activities(
    keyword: Optional[str] = None,
    start_after: Optional[str] = None,
    start_before: Optional[str] = None,
    limit: int = 10,
    **kwargs
) -> Dict[str, Any]:
    """
    执行 search_activities：查询社交活动
    """
    try:
        from activities.models import Activity
        from datetime import datetime

        limit = min(int(limit), 50)
        qs = Activity.objects.filter(status__in=[1, 2])  # 报名中/进行中

        if keyword:
            qs = (qs.filter(title__icontains=keyword) | qs.filter(description__icontains=keyword))

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

        results = list(qs.select_related('organizer')[:limit])

        items = []
        for a in results:
            items.append({
                "uuid": str(a.uuid),
                "title": a.title,
                "description": a.description[:200] if a.description else "",
                "activity_type": a.activity_type,
                "location": a.location,
                "start_time": a.start_time.isoformat() if a.start_time else None,
                "fee": str(a.fee) if a.fee else None,
                "enrollment_mode": a.enrollment_mode,
                "organizer_name": a.organizer.real_name if a.organizer else "",
                "current_attendees": a.current_attendees,
            })
        return {"items": items, "total": len(items)}
    except Exception as e:
        logger.exception(f"[tools] search_activities error: {e}")
        return {"items": [], "total": 0, "error": str(e)}


# 工具名 -> 函数映射
TOOL_HANDLERS = {
    "search_supplies": exec_search_supplies,
    "search_profiles": exec_search_profiles,
    "search_activities": exec_search_activities,
}


def execute_tool(tool_call: Dict[str, Any]) -> Dict[str, Any]:
    """
    根据 tool_call 执行对应的本地工具
    tool_call 格式: {"name": "search_supplies", "arguments": {"keyword": "投资", "limit": 5}}
    返回 {"result": <执行结果>}
    """
    name = tool_call.get("name", "")
    raw_args = tool_call.get("arguments", {})

    # arguments可能是字符串JSON，需要解析
    if isinstance(raw_args, str):
        try:
            args = json.loads(raw_args)
        except json.JSONDecodeError:
            return {"result": {"error": f"无法解析参数: {raw_args}"}}
    else:
        args = raw_args

    handler = TOOL_HANDLERS.get(name)
    if not handler:
        return {"result": {"error": f"未知工具: {name}"}}

    try:
        result = handler(**args)
        return {"result": result}
    except Exception as e:
        logger.exception(f"[tools] execute_tool {name} error: {e}")
        return {"result": {"error": str(e)}}