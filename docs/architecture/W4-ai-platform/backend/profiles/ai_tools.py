"""
本 app 暴露给 AI 的工具 - 校友档案/名片搜索
"""
from django.db.models import Q

SCHEMA = {
    "type": "function",
    "function": {
        "name": "search_profiles",
        "description": (
            "搜索校友/用户档案，支持按行业、职位、学校、城市过滤。"
            "默认只返回已通过认证的用户。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "industry": {
                    "type": "string",
                    "description": "行业关键词，如：互联网、金融、医疗",
                },
                "position": {
                    "type": "string",
                    "description": "职位关键词",
                },
                "school": {
                    "type": "string",
                    "description": "毕业学校名称",
                },
                "city": {
                    "type": "string",
                    "description": "所在城市",
                },
                "cert_status": {
                    "type": "integer",
                    "default": 2,
                    "description": "认证状态（2=已认证，0=待审核，1=审核中）",
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


def handler(industry=None, position=None, school=None, city=None,
            cert_status=2, limit=10, **kwargs):
    """执行 search_profiles"""
    from .models import Profile

    limit = min(int(limit), 50)
    qs = Profile.objects.select_related('user')

    # 默认只返回已认证的
    if cert_status is not None:
        qs = qs.filter(cert_status=int(cert_status))

    if industry:
        qs = qs.filter(industry__icontains=industry)
    if position:
        qs = qs.filter(position__icontains=position)
    if school:
        qs = qs.filter(education_school__icontains=school)
    if city:
        qs = qs.filter(city__icontains=city)

    results = list(qs[:limit])

    items = []
    for p in results:
        user = getattr(p, 'user', None)
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
            "cert_status": p.cert_status,
            "avatar_url": getattr(user, 'avatar_url', '') if user else '',
        })

    return {"items": items, "total": len(items)}