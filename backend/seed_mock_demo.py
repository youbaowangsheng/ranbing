"""
Mock 演示数据 seed 脚本（生产环境可用，幂等）

作用：
1. 激活现有 supply（audit_status=1 审核通过）让首页瀑布流有数据
2. 新增一批 supply / activity / community message 让页面丰满
3. 补充 profile 的 company/position/industry 等字段
4. 为 profile 补 profile_tags

用法（在服务器上，/www/ranbing 目录）：
  cd /www/ranbing && python3.11 seed_mock_demo.py

幂等：可重复运行，已存在的跳过。
"""
import os
import sys
import django
from datetime import timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ranbing.settings')
# 不覆盖 DB_ENGINE 等，直接用生产 settings（MySQL qy_mobile）
django.setup()

from django.utils import timezone
from users.models import User
from profiles.models import Profile, ProfileTag, Tag
from supplies.models import Supply
from communities.models import Community, CommunityMember, Message
from activities.models import Activity

# ── 1. 激活现有 supply ───────────────────────────────────────
activated = Supply.objects.filter(audit_status=0).update(
    audit_status=1,
    status=1,
    audit_time=timezone.now(),
)
print(f'✅ 激活 supply（audit_status 0→1）: {activated} 条')

# ── 2. 补充现有 profile 的字段 ───────────────────────────────
profile_updates = 0
for p in Profile.objects.all():
    changed = False
    if not p.company:
        p.company = '燃冰科技'
        changed = True
    if not p.position:
        p.position = '创始人'
        changed = True
    if not p.industry:
        p.industry = '企业服务'
        changed = True
    if not p.city:
        p.city = '北京'
        changed = True
    if changed:
        p.save(update_fields=['company', 'position', 'industry', 'city'])
        profile_updates += 1
print(f'✅ 补充 profile 字段: {profile_updates} 个')

# ── 3. Tag 映射 ─────────────────────────────────────────────
tag_map = {t.name: t.id for t in Tag.objects.all()}
print(f'   Tag 总数: {len(tag_map)}')

def tag_ids(names):
    return [tag_map[n] for n in names if n in tag_map]

# ── 4. 新增 demo supply ─────────────────────────────────────
# 用现有 profile 轮换，确保每条 supply 都有有效作者
profiles = list(Profile.objects.all())
if not profiles:
    print('⚠️ 没有 profile，跳过新增 supply')
    profiles = []

demo_supplies = [
    (1, '企业服务 SaaS 客户资源对接', '专注企业服务 B2B 赛道，拥有 50+ 优质客户资源，涵盖 SaaS、咨询、外包等类型，欢迎有企业客户需求的朋友合作。', ['企业服务', '优质客户', '渠道分销']),
    (1, '消费品牌全渠道增长方案', '10 年品牌增长经验，擅长线上+线下全渠道整合，曾操盘多个千万级项目，可为早期消费品牌提供增长咨询。', ['消费零售', '渠道分销', '品牌弱']),
    (1, '企业服务赛道投资机会', '专注企业服务早期投资，聚焦 A 轮到 B 轮阶段，单笔投资 500-3000 万，已投 10+ 企业服务项目。', ['投资机构', '资本支持']),
    (2, '急求：工业品销售渠道合作', '工厂数字化产品已完成研发，已有两家头部客户落地，正在扩展工业品渠道，希望找有工厂/制造业渠道资源的伙伴合作。', ['先进制造', '销售商务', '供应链']),
    (1, '企业服务融资 FA 服务', '专注企业服务赛道，深度理解 SaaS 指标体系，曾帮助 3 家 SaaS 公司完成从天使到 B 轮融资。', ['金融科技', '投资机构', '融资需求']),
    (2, '寻找品牌设计校友合作', '需要品牌 VI 设计和产品视觉优化资源，预算有限，希望找有经验且愿意尝试企业服务方向的校友合作。', ['企业服务', '设计创意', '品牌弱']),
    (1, '医疗健康数字化转型方案', '专注医疗健康行业，提供药械数字化、患者管理、供应链优化等解决方案，已落地 20+ 医疗机构。', ['医疗健康', '技术开发', '优质客户']),
    (2, '寻找跨境电商供应链资源', '正在做跨境电商业务，需要稳定的供应链和物流资源，希望找有海外仓或跨境物流经验的朋友。', ['消费零售', '供应链', '国际化']),
    (1, 'AI 大模型行业解决方案', '提供基于大模型的行业定制方案，覆盖金融、教育、政务等场景，可提供私有化部署和 API 服务。', ['企业服务', '技术开发', '数据资产']),
    (2, '招聘：高级后端工程师', '创业公司招聘高级后端工程师，熟悉 Python/Django 或 Go，有分布式系统经验，可远程。', ['招人困难', '产品研发', '技术极客']),
    (1, '政府补贴申报咨询服务', '提供高新技术企业、专精特新等政府补贴申报咨询，成功率高，已帮助 100+ 企业获得补贴。', ['政务资源', '财税优化', '培训咨询']),
    (2, '寻找法律合规顾问', '公司正在融资，需要法律合规顾问协助梳理股权结构、合同审查等。', ['法律合规', '融资需求', '财务法务']),
    (1, '教育行业课程内容合作', '拥有优质教育课程内容资源，覆盖 K12、职业教育、成人培训等，欢迎渠道合作。', ['文化教育', '渠道分销', '内容出版'] if '文化教育' in tag_map else ['企业服务', '渠道分销']),
    (2, '寻找投资机构对接', '成长期企业，营收稳定增长，正在寻找 B 轮融资，希望对接靠谱投资机构。', ['投资机构', '融资需求', '投资行家']),
    (1, '企业出海东南亚服务', '提供企业出海东南亚的全套服务，包括公司注册、本地化运营、市场拓展等。', ['国际化', '渠道分销', '优质客户']),
    (2, '寻找社群运营合作伙伴', '正在搭建行业社群，寻找有社群运营经验的朋友合作，一起做内容和服务。', ['社群网络', '运营管理', '培训咨询']),
    (1, '数据中台建设方案', '提供企业数据中台建设方案，涵盖数据治理、数据仓库、BI 可视化等，服务过大中型企业。', ['数据资产', '技术开发', '企业服务']),
    (2, '寻找财税优化服务', '小微企业，想了解财税优化和合规筹划，希望找靠谱的财税顾问。', ['财税优化', '财务法务', '融资需求']),
    (1, '线下沙龙活动场地资源', '可提供北京、上海等地线下活动场地资源，适合举办行业沙龙、路演等。', ['办公资源', '社群网络', '渠道分销']),
    (2, '寻找技术合伙人', '有想法和客户资源，正在寻找技术合伙人，一起做企业服务方向的创业项目。', ['招人困难', '技术开发', '连续创业者']),
]

created_supply = 0
for i, (stype, title, content, tags) in enumerate(demo_supplies):
    profile = profiles[i % len(profiles)]
    tids = tag_ids(tags)
    _, created = Supply.objects.get_or_create(
        profile=profile,
        title=title,
        defaults={
            'supply_type': stype,
            'content': content,
            'tags': tids,
            'audit_status': 1,
            'status': 1,
            'audit_time': timezone.now(),
            'view_count': 30 + i * 7,
            'match_count': 2 + i % 5,
            'quality_score': 0.65 + (i % 4) * 0.08,
            'expires_at': timezone.now() + timedelta(days=30),
        }
    )
    if created:
        created_supply += 1

print(f'✅ 新增 supply: {created_supply} 条')
print(f'   当前 supply 总数: {Supply.objects.count()}')
print(f'   审核通过 supply: {Supply.objects.filter(audit_status=1, status=1).count()}')

# ── 5. 新增 demo activity（如果活动太少）─────────────────────
act_count = Activity.objects.filter(status=1).count()
if act_count < 10:
    demo_activities = [
        ('AI 与企业服务创新沙龙', '探讨 AI 大模型在企业服务领域的落地应用，邀请行业专家分享实战案例。', 1, '北京', '线下'),
        ('消费品牌增长私享会', '聚焦消费品牌增长方法论，分享私域运营、全渠道布局经验。', 2, '上海', '线下'),
        ('SaaS 创业者的融资之道', '邀请投资人和创业者，聊聊 SaaS 企业如何顺利融资。', 2, '北京', '线上'),
        ('制造业数字化转型实战', '制造业数字化转型案例分享，覆盖工厂智能化、供应链优化。', 3, '深圳', '线下'),
        ('跨境电商出海经验分享', '跨境电商卖家交流出海经验，分享供应链和物流资源。', 4, '杭州', '线上'),
    ]
    created_act = 0
    for (title, desc, atype, city, mode) in demo_activities:
        # 找 organizer（第一个有 profile 的）
        organizer = profiles[0] if profiles else None
        if not organizer:
            break
        _, created = Activity.objects.get_or_create(
            title=title,
            defaults={
                'organizer': organizer,
                'description': desc,
                'activity_type': atype,
                'location': city + '市中心',
                'enrollment_mode': 1,
                'audit_status': 1,
                'status': 1,
                'start_time': timezone.now() + timedelta(days=7),
                'end_time': timezone.now() + timedelta(days=7, hours=3),
                'current_attendees': 5 + created_act * 3,
            }
        )
        if created:
            created_act += 1
    print(f'✅ 新增 activity: {created_act} 条')

# ── 6. 补 community message（如果社群消息太少）───────────────
msg_count = Message.objects.count()
if msg_count < 30:
    demo_msgs = [
        '大家好，我是做企业服务的，欢迎交流合作机会',
        '最近在找投资机构对接，有资源的同学可以聊聊',
        '分享一个观点：AI 时代企业服务的核心是效率提升',
        '有没有做跨境电商的朋友，想交流下供应链',
        '本周末北京有 AI 沙龙，感兴趣的可以报名',
        '推荐一本好书《增长黑客》，做增长的朋友值得一读',
        '公司招人，高级后端工程师，远程可谈',
        '刚参加完一场行业路演，收获很大，整理下分享',
        '有做财税的朋友吗？想咨询下合规筹划',
        '欢迎新朋友，大家介绍下自己吧',
    ]
    communities = list(Community.objects.filter(status__in=[1, 2]))
    created_msg = 0
    if communities and profiles:
        for i, text in enumerate(demo_msgs):
            comm = communities[i % len(communities)]
            profile = profiles[i % len(profiles)]
            # 确保 profile 在社群（或跳过）
            _, _ = CommunityMember.objects.get_or_create(community=comm, profile=profile)
            _, created = Message.objects.get_or_create(
                community=comm,
                profile=profile,
                content=text,
                defaults={'audit_status': 1}
            )
            if created:
                created_msg += 1
        print(f'✅ 新增 community message: {created_msg} 条')
    else:
        print('⚠️ 无社群或 profile，跳过消息')

print()
print('=== Mock 数据完成 ===')
print(f'  Supply 审核通过: {Supply.objects.filter(audit_status=1, status=1).count()}')
print(f'  Activity: {Activity.objects.count()}')
print(f'  Community: {Community.objects.count()}')
print(f'  Message: {Message.objects.count()}')
print(f'  Profile: {Profile.objects.count()}')
