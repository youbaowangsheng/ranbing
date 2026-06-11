"""
Seed demo 用户 + 供需数据
"""
import os, sys, django

# 强制设 env（优先级最高）
os.environ['DB_ENGINE'] = 'django.db.backends.postgresql'
os.environ['DB_NAME'] = 'fipai'
os.environ['DB_USER'] = 'fipai'
os.environ['DB_PASSWORD'] = 'fipai'
os.environ['DB_HOST'] = 'localhost'
os.environ['DB_PORT'] = '5432'
os.environ['JWT_SECRET_KEY'] = 'ranbing-dev-secret-key-2026'
os.environ['JWT_ACCESS_TOKEN_LIFETIME'] = '604800'
os.environ['JWT_REFRESH_TOKEN_LIFETIME'] = '2592000'
os.environ['SMS_PROVIDER'] = 'mock'
os.environ['DEEPSEEK_API_KEY'] = 'mock-key'
os.environ['DEBUG'] = 'true'

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ranbing.settings')
django.setup()

from users.models import User
from profiles.models import Profile, ProfileTag, Tag
from supplies.models import Supply
import uuid

# ── Demo 用户 ────────────────────────────────────────────────
demo_users = [
    {'phone': '13800138001', 'nickname': '王建', 'avatar': 'https://api.dicebear.com/7.x/avataaars/svg?seed=w1',
     'real_name': '王建', 'company': '云智科技', 'position': '创始人', 'industry': '企业服务',
     'city': '北京', 'bio': '连续创业者，专注企业服务赛道，已服务50+客户',
     'edu_year': '2022', 'edu_school': '清华大学', 'edu_major': '计算机系',
     'cert_level': 3, 'conn_count': 89, 'active_score': 92.5},
    {'phone': '13800138002', 'nickname': '张伟', 'avatar': 'https://api.dicebear.com/7.x/avataaars/svg?seed=z1',
     'real_name': '张伟', 'company': '华创资本', 'position': '合伙人', 'industry': '投资机构',
     'city': '北京', 'bio': '专注企业服务领域投资，成功投资10+项目',
     'edu_year': '2018', 'edu_school': '复旦大学', 'edu_major': '金融系',
     'cert_level': 3, 'conn_count': 156, 'active_score': 88.0},
    {'phone': '13800138003', 'nickname': '李娜', 'avatar': 'https://api.dicebear.com/7.x/avataaars/svg?seed=l1',
     'real_name': '李娜', 'company': '品创品牌咨询', 'position': '合伙人', 'industry': '消费零售',
     'city': '上海', 'bio': '10年品牌营销经验，专注消费品增长',
     'edu_year': '2018', 'edu_school': '北京大学', 'edu_major': '市场营销',
     'cert_level': 3, 'conn_count': 67, 'active_score': 78.5},
    {'phone': '13800138004', 'nickname': '王强', 'avatar': 'https://api.dicebear.com/7.x/avataaars/svg?seed=w2',
     'real_name': '王强', 'company': '鼎新制造', 'position': '技术VP', 'industry': '先进制造',
     'city': '上海', 'bio': '制造业数字化转型专家，有丰富工厂资源',
     'edu_year': '2020', 'edu_school': '上海交通大学', 'edu_major': '机械工程',
     'cert_level': 2, 'conn_count': 45, 'active_score': 65.0},
    {'phone': '13800138005', 'nickname': '陈思', 'avatar': 'https://api.dicebear.com/7.x/avataaars/svg?seed=c1',
     'real_name': '陈思', 'company': '投顾资本', 'position': '市场总监', 'industry': '金融科技',
     'city': '上海', 'bio': '专注企业服务FA，深度理解SaaS指标体系',
     'edu_year': '2019', 'edu_school': '上海交通大学', 'edu_major': '工商管理',
     'cert_level': 3, 'conn_count': 98, 'active_score': 81.0},
]

# tag_id mapping by name
tag_map = {t.name: t.id for t in Tag.objects.all()}

def get_tag_ids(names):
    return [tag_map[n] for n in names if n in tag_map]

# tag_type: 1=供给 2=需求
user_tags = {
    '王建':       {'supply': ['企业服务','技术开发','优质客户'], 'demand': ['品牌弱','融资需求']},
    '张伟':       {'supply': ['资本支持'], 'demand': []},
    '李娜':       {'supply': ['渠道分销','品牌增长'], 'demand': ['融资需求','技术开发']},
    '王强':       {'supply': ['供应链','优质客户'], 'demand': ['销售渠道','品牌弱']},
    '陈思':       {'supply': ['投资机构'], 'demand': ['优质客户']},
}

created_users = {}
for udata in demo_users:
    phone = udata['phone']
    try:
        user = User.objects.get(phone=phone)
        created = False
    except User.DoesNotExist:
        user = User.objects.create_user(phone=phone, nickname=udata['nickname'], is_verified=True)
        user.avatar_url = udata['avatar']
        user.save(update_fields=['avatar_url'])
        created = True
    created_users[phone] = user

    if created:
        profile = Profile.objects.create(user=user,
            real_name=udata['real_name'], company=udata['company'],
            position=udata['position'], industry=udata['industry'],
            city=udata['city'], bio=udata['bio'],
            education_year=udata['edu_year'], education_school=udata['edu_school'],
            education_major=udata['edu_major'], cert_level=udata['cert_level'],
            conn_count=udata['conn_count'], active_score=udata['active_score'])
    else:
        profile, profile_created = Profile.objects.get_or_create(
            user_id=user.id,
            defaults={
                'real_name': udata['real_name'], 'company': udata['company'],
                'position': udata['position'], 'industry': udata['industry'],
                'city': udata['city'], 'bio': udata['bio'],
                'education_year': udata['edu_year'], 'education_school': udata['edu_school'],
                'education_major': udata['edu_major'], 'cert_level': udata['cert_level'],
                'conn_count': udata['conn_count'], 'active_score': udata['active_score'],
            }
        )
    # Profile tags
    tags = user_tags.get(udata['real_name'], {'supply': [], 'demand': []})
    for tag_name in tags.get('supply', []):
        if tag_name in tag_map:
            ProfileTag.objects.get_or_create(profile=profile, tag_id=tag_map[tag_name],
                                            defaults={'tag_type': 1})
    for tag_name in tags.get('demand', []):
        if tag_name in tag_map:
            ProfileTag.objects.get_or_create(profile=profile, tag_id=tag_map[tag_name],
                                            defaults={'tag_type': 2})

print(f'✅ Users seeded: {len(created_users)}')

# ── Demo 供需 ────────────────────────────────────────────────
supplies_data = [
    {'phone': '13800138001', 'supply_type': 1, 'title': '企业服务客户资源对接',
     'content': '专注企业服务B2B赛道，有50+客户资源可对接，包含SaaS、咨询、外包等类型，欢迎有企业客户需求的朋友合作。',
     'tags': ['企业服务','优质客户','渠道分销']},
    {'phone': '13800138002', 'supply_type': 1, 'title': '企业服务赛道投资机会',
     'content': '华创资本专注企业服务早期投资，聚焦A轮到B轮阶段，单笔投资500-3000万，已投10+企业服务项目。',
     'tags': ['投资机构','资本支持']},
    {'phone': '13800138003', 'supply_type': 1, 'title': '消费品牌全渠道增长方案',
     'content': '10年品牌增长经验，擅长线上+线下全渠道整合，曾操盘多个千万级项目，可为早期消费品牌提供增长咨询。',
     'tags': ['消费零售','渠道分销','品牌增长']},
    {'phone': '13800138004', 'supply_type': 2, 'title': '急求：工业品销售渠道合作',
     'content': '工厂数字化产品已完成研发，已有两家头部客户落地，正在扩展工业品渠道，希望找有工厂/制造业渠道资源的伙伴合作。',
     'tags': ['先进制造','销售渠道','供应链']},
    {'phone': '13800138005', 'supply_type': 1, 'title': '企业服务融资FA服务',
     'content': '专注企业服务赛道，深度理解SaaS指标体系，曾帮助3家SaaS公司完成从天使到B轮融资，对接过多家头部VC机构。',
     'tags': ['金融科技','投资机构','融资需求']},
    {'phone': '13800138001', 'supply_type': 2, 'title': '寻找能做品牌设计的校友',
     'content': '需要品牌vi设计和产品视觉优化资源，预算有限，希望找有经验且愿意尝试企业服务方向的校友合作。',
     'tags': ['企业服务','品牌弱']},
]

for sdata in supplies_data:
    user = created_users[sdata.pop('phone')]
    profile = user.profile
    tag_names = sdata.pop('tags', [])
    tag_ids = get_tag_ids(tag_names)
    s, created = Supply.objects.get_or_create(
        profile=profile,
        title=sdata['title'],
        defaults={**sdata, 'tags': tag_ids, 'view_count': 50, 'match_count': 5}
    )
    if created:
        print(f'  + Supply: {s.title}')

print(f'✅ Demo supplies seeded')
print(f'   Total supplies: {Supply.objects.count()}')
print(f'   Total profiles: {Profile.objects.count()}')
