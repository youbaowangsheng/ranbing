"""给测试 profile 换上有真实感的名字/公司/职位，让演示页面更专业"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ranbing.settings')
django.setup()

from profiles.models import Profile

# 真实感的商务人物资料（行业多样性）
demo_profiles = [
    ('王建', '云智科技', '创始人兼CEO', '企业服务', '北京'),
    ('张伟', '华创资本', '合伙人', '投资机构', '北京'),
    ('李娜', '品创品牌咨询', '合伙人', '消费零售', '上海'),
    ('王强', '鼎新制造', '技术副总裁', '先进制造', '深圳'),
    ('陈思', '投顾资本', '市场总监', '金融科技', '上海'),
    ('刘洋', '数联科技', '创始人', '企业服务', '杭州'),
    ('赵敏', '康泰医疗', '商务总监', '医疗健康', '北京'),
    ('孙磊', '出海通', '联合创始人', '跨境电商', '广州'),
    ('周杰', '启明创投', '投资经理', '投资机构', '深圳'),
    ('吴婷', '蓝标公关', '品牌顾问', '消费零售', '上海'),
    ('郑浩', '智造工厂', '总经理', '先进制造', '苏州'),
    ('冯雪', '悦己教育', '创始人', '文化教育', '成都'),
]

profiles = list(Profile.objects.order_by('id'))

updated = 0
for i, p in enumerate(profiles):
    name, company, pos, industry, city = demo_profiles[i % len(demo_profiles)]
    p.real_name = name
    p.company = company
    p.position = pos
    p.industry = industry
    p.city = city
    p.save(update_fields=['real_name', 'company', 'position', 'industry', 'city'])
    updated += 1

print(f'✅ 更新 {updated} 个 profile 为真实感资料')
for p in Profile.objects.order_by('id'):
    print(f'  {p.real_name} @ {p.company} ({p.position}) - {p.industry}/{p.city}')
