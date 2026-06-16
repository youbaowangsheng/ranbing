"""
Seed 100核心标签数据到 PostgreSQL
"""
import os, sys, django

os.environ['DB_ENGINE'] = 'django.db.backends.postgresql'
os.environ['DB_NAME'] = 'fipai'
os.environ['DB_USER'] = 'fipai'
os.environ['DB_PASSWORD'] = os.environ.get('DB_PASSWORD', 'fipai')
os.environ['DB_HOST'] = 'localhost'
os.environ['DB_PORT'] = '5432'
os.environ['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'ranbing-dev-secret-key-2026')
os.environ['JWT_ACCESS_TOKEN_LIFETIME'] = '604800'
os.environ['JWT_REFRESH_TOKEN_LIFETIME'] = '2592000'
os.environ['SMS_PROVIDER'] = 'mock'
os.environ['DEEPSEEK_API_KEY'] = 'mock-key'
os.environ['DEBUG'] = 'true'

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ranbing.settings')
django.setup()

from profiles.models import Tag

# L1 行业标签
l1_industries = [
    ('创业企业', '创始人/联合创始人', 3),
    ('投资机构', 'VC/PE/天使', 3),
    ('企业服务', 'SaaS/咨询/外包', 3),
    ('消费零售', '品牌/渠道/电商', 3),
    ('医疗健康', '药械/服务/IT', 3),
    ('金融科技', '支付/银行/保险科技', 3),
    ('先进制造', '硬科技/供应链', 3),
    ('文化教育', '教育/内容/出版', 3),
    ('房地产建筑', '开发/设计/装修', 3),
    ('政府公益', '事业单位/NGO', 3),
]

# L2 职能标签
l2_functions = [
    ('企业战略', 'CEO/战略/投融资', 3),
    ('市场营销', '品牌/增长/内容', 3),
    ('产品研发', '产品/技术/数据', 3),
    ('销售商务', '销售/渠道/大客户', 3),
    ('运营管理', '运营/HR/行政', 3),
    ('财务法务', '财务/法务/合规', 3),
    ('投资投行', '投资/并购/FA', 3),
    ('科研教育', '学术/教授/研究员', 3),
    ('媒体公关', '媒体/传播/政府关系', 3),
    ('设计创意', 'UI/UX/品牌设计', 3),
]

# L3 资源能力标签
l3_resources = [
    ('资本支持', '供给资源', '资本支持', '', '', 1),
    ('优质客户', '供给资源', '优质客户', '', '', 1),
    ('技术开发', '供给资源', '技术开发', '', '', 1),
    ('渠道分销', '供给资源', '渠道分销', '', '', 1),
    ('媒体资源', '供给资源', '媒体资源', '', '', 1),
    ('人才推荐', '供给资源', '人才推荐', '', '', 1),
    ('供应链', '供给资源', '供应链', '', '', 1),
    ('政务资源', '供给资源', '政务资源', '', '', 1),
    ('法律合规', '供给资源', '法律合规', '', '', 1),
    ('财税优化', '供给资源', '财税优化', '', '', 1),
    ('数据资产', '供给资源', '数据资产', '', '', 1),
    ('培训咨询', '供给资源', '培训咨询', '', '', 1),
    ('办公资源', '供给资源', '办公资源', '', '', 1),
    ('社群网络', '供给资源', '社群网络', '', '', 1),
    ('国际化', '供给资源', '国际化', '', '', 1),
    ('融资需求', '需求帮助', '融资需求', '', '', 2),
    ('销售困难', '需求帮助', '销售困难', '', '', 2),
    ('招人困难', '需求帮助', '招人困难', '', '', 2),
    ('品牌弱', '需求帮助', '品牌弱', '', '', 2),
    ('供应链难', '需求帮助', '供应链难', '', '', 2),
]

# L4 身份背景标签
l4_identity = [
    ('连续创业者', '行业经验', '连续创业者', '', '', 3),
    ('核心二次创业', '行业经验', '核心二次创业', '', '', 3),
    ('科研背景', '行业经验', '科研背景', '', '', 3),
    ('海归背景', '行业经验', '海归背景', '', '', 3),
    ('投资行家', '行业经验', '投资行家', '', '', 3),
    ('行业老兵', '行业经验', '行业老兵', '', '', 3),
    ('上市公司高管', '行业经验', '上市公司高管', '', '', 3),
    ('国企背景', '行业经验', '国企背景', '', '', 3),
    ('家族企业', '行业经验', '家族企业', '', '', 3),
    ('自由职业', '行业经验', '自由职业', '', '', 3),
]

# L5 兴趣社交标签
l5_social = [
    ('创业投资', '社交兴趣', '创业投资', '', '', 3),
    ('技术极客', '社交兴趣', '技术极客', '', '', 3),
    ('户外运动', '社交兴趣', '户外运动', '', '', 3),
    ('读书分享', '社交兴趣', '读书分享', '', '', 3),
    ('美食探店', '社交兴趣', '美食探店', '', '', 3),
    ('文艺生活', '社交兴趣', '文艺生活', '', '', 3),
    ('亲子时光', '社交兴趣', '亲子时光', '', '', 3),
    ('公益慈善', '社交兴趣', '公益慈善', '', '', 3),
    ('高尔夫', '社交兴趣', '高尔夫', '', '', 3),
    ('茶道收藏', '社交兴趣', '茶道收藏', '', '', 3),
]

all_tags = []

# L1: name, l1_category, l2_group
for name, desc, tt in l1_industries:
    all_tags.append(Tag(name=name, l1_category=name, l2_group=desc, tag_type=tt))

# L2: name, l1_category, l2_group
for name, desc, tt in l2_functions:
    all_tags.append(Tag(name=name, l1_category=name, l2_group=desc, tag_type=tt))

# L3: name, l1, l2, l3, l4, tag_type
for name, l1, l2, l3, l4, tt in l3_resources:
    all_tags.append(Tag(name=name, l1_category=l1, l2_group=l2, tag_type=tt))

# L4/L5: name, l1, l2, l3, l4, tag_type
for name, l1, l2, l3, l4, tt in l4_identity + l5_social:
    all_tags.append(Tag(name=name, l1_category=l1, l2_group=l2, tag_type=tt))

created = 0
for t in all_tags:
    obj, was_created = Tag.objects.get_or_create(name=t.name, defaults={
        'l1_category': t.l1_category,
        'l2_group': t.l2_group,
        'l3_item': t.l3_item,
        'l4_attr': t.l4_attr,
        'l5_detail': t.l5_detail,
        'tag_type': t.tag_type,
    })
    if was_created:
        created += 1

print(f'✅ Tags seeded: {created}/{len(all_tags)} new tags created (existing skipped)')
print(f'   Total tags in DB: {Tag.objects.count()}')
