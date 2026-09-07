"""补丁：给已有 supply 回填 tags（因为之前 tag 表为空，tags 是空列表）"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ranbing.settings')
django.setup()

from supplies.models import Supply
from profiles.models import Tag

tag_map = {t.name: t.id for t in Tag.objects.all()}

# 标题关键词 → 标签映射
keyword_tags = {
    '企业服务': ['企业服务', '优质客户'],
    'SaaS': ['企业服务', '技术开发'],
    '消费': ['消费零售', '渠道分销'],
    '品牌': ['消费零售', '设计创意'],
    '投资': ['投资机构', '资本支持'],
    '融资': ['融资需求', '投资机构'],
    '制造': ['先进制造', '供应链'],
    '工业': ['先进制造', '供应链'],
    '渠道': ['渠道分销', '销售商务'],
    '医疗': ['医疗健康', '技术开发'],
    '跨境': ['消费零售', '国际化'],
    '出海': ['国际化', '渠道分销'],
    'AI': ['企业服务', '技术开发'],
    '大模型': ['企业服务', '技术开发'],
    '招聘': ['招人困难', '人才推荐'],
    '工程师': ['招人困难', '产品研发'],
    '政府': ['政务资源', '财税优化'],
    '补贴': ['政务资源', '财税优化'],
    '法律': ['法律合规', '财务法务'],
    '合规': ['法律合规', '财务法务'],
    '教育': ['文化教育', '渠道分销'],
    '数据': ['数据资产', '技术开发'],
    '财税': ['财税优化', '财务法务'],
    '社群': ['社群网络', '运营管理'],
    '沙龙': ['社群网络', '办公资源'],
    '技术合伙人': ['招人困难', '技术开发'],
    '创始人': ['连续创业者', '创业企业'],
}

def suggest_tags(title, content):
    text = title + ' ' + (content or '')
    result = []
    for kw, tagnames in keyword_tags.items():
        if kw in text:
            for tn in tagnames:
                if tn in tag_map and tn not in result:
                    result.append(tn)
    return result

updated = 0
for s in Supply.objects.all():
    if s.tags and len(s.tags) > 0:
        continue  # 已有 tags
    names = suggest_tags(s.title, s.content)
    tids = [tag_map[n] for n in names if n in tag_map]
    if tids:
        s.tags = tids
        s.save(update_fields=['tags'])
        updated += 1

print(f'Backfill supply tags: {updated} 条更新')
print(f'  有 tags 的 supply: {Supply.objects.exclude(tags=[]).count()}/{Supply.objects.count()}')
