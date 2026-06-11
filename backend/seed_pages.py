import os, sys, django, datetime
sys.path.insert(0, '/Users/wangsheng/ranbing/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ranbing.settings')
django.setup()

from django.utils import timezone
from activities.models import Activity, ActivityEnrollment
from communities.models import Community, CommunityMember
from supplies.models import Supply
from profiles.models import Profile
from decimal import Decimal

now = timezone.now()

# ── 清理旧数据 ──
Activity.objects.all().delete()
Community.objects.all().delete()
CommunityMember.objects.all().delete()
ActivityEnrollment.objects.all().delete()

# ── 6个活动 ──
activities_data = [
    {"title": "AI驱动企业数字化转型分享会", "desc": "探讨大模型如何落地制造/零售/金融场景",
     "type": 1, "school": "复旦大学", "location": "上海市杨浦区国年路286号",
     "start": now+datetime.timedelta(days=3), "end": now+datetime.timedelta(days=3,hours=3),
     "fee": "0", "max": 100, "tags": [1,2,3]},
    {"title": "医疗健康产业投资私享会", "desc": "闭门分享医疗器械/创新药投资逻辑",
     "type": 1, "school": "上海交通大学", "location": "上海市徐汇区华山路1954号",
     "start": now+datetime.timedelta(days=7), "end": now+datetime.timedelta(days=7,hours=2),
     "fee": "200", "max": 30, "tags": [4,5]},
    {"title": "消费品牌出海实战工作坊", "desc": "Shopify/TikTok渠道避坑指南",
     "type": 2, "school": "中欧国际工商学院", "location": "上海市浦东新区红枫路699号",
     "start": now+datetime.timedelta(days=14), "end": now+datetime.timedelta(days=14,hours=4),
     "fee": "500", "max": 50, "tags": [6,7]},
    {"title": "创业者融资路演日", "desc": "10个优质早期项目对接50+机构投资人",
     "type": 3, "school": "清华大学", "location": "北京市海淀区双清路30号",
     "start": now+datetime.timedelta(days=5), "end": now+datetime.timedelta(days=5,hours=5),
     "fee": "0", "max": 200, "tags": [1,8]},
    {"title": "ESG可持续发展峰会", "desc": "碳中和政策解读与绿色金融机遇",
     "type": 1, "school": "北京大学", "location": "北京市海淀区颐和园路5号",
     "start": now+datetime.timedelta(days=10), "end": now+datetime.timedelta(days=10,hours=6),
     "fee": "800", "max": 150, "tags": [9,10]},
    {"title": "芯片半导体供应链对接会", "desc": "国产替代机遇下的供应商精准匹配",
     "type": 3, "school": "浙江大学", "location": "杭州市西湖区余杭塘路866号",
     "start": now+datetime.timedelta(days=21), "end": now+datetime.timedelta(days=21,hours=3),
     "fee": "100", "max": 80, "tags": [11,12]},
]

profiles = list(Profile.objects.select_related('user').all())
for i, a in enumerate(activities_data):
    organizer = profiles[i % len(profiles)]
    act = Activity.objects.create(
        title=a["title"], description=a["desc"], activity_type=a["type"],
        organizer=organizer, host_school=a["school"], location=a["location"],
        start_time=a["start"], end_time=a["end"], max_attendees=a["max"],
        current_attendees=0, enrollment_mode=1, fee=Decimal(a["fee"]),
        tags=a["tags"], status=1, ai_match_enabled=True,
    )
    enrolled = 0
    for j, p in enumerate(profiles):
        if j == i: continue
        if enrolled >= 5: break
        ActivityEnrollment.objects.create(
            activity=act, profile=p, enrollment_status=1,
            ai_recommended=False, ai_match_score=Decimal("0.75"),
        )
        act.current_attendees += 1
        enrolled += 1
    act.save()
    print(f"Activity: {act.title[:30]} (enrolled={act.current_attendees})")

# ── 5个社群 ──
communities_data = [
    {"name": "复旦AI创业者联盟", "desc": "聚焦人工智能创业与投资，连接复旦系创业者与投资人",
     "type": 1, "school": "复旦大学", "members": 128},
    {"name": "医疗健康投资圈", "desc": "医疗器械+创新药+医疗服务，投资逻辑分享",
     "type": 1, "school": "上海交通大学", "members": 256},
    {"name": "消费品牌出海圈", "desc": "品牌出海实战案例、渠道资源对接",
     "type": 2, "school": "中欧国际工商学院", "members": 89},
    {"name": "半导体产业协作网络", "desc": "芯片设计/制造/封测全链条从业者社群",
     "type": 1, "school": "清华大学", "members": 174},
    {"name": "ESG与绿色金融", "desc": "碳中和、ESG评级、绿色债券讨论",
     "type": 2, "school": "北京大学", "members": 67},
]

for i, c in enumerate(communities_data):
    owner = profiles[i % len(profiles)]
    comm = Community.objects.create(
        name=c["name"], description=c["desc"], community_type=c["type"],
        school=c["school"], cover_url="", member_count=c["members"],
        owner=owner, status=1,
    )
    for j, p in enumerate(profiles):
        role = 1 if p == owner else 2
        CommunityMember.objects.create(
            community=comm, profile=p, role=role, status=1,
        )
    print(f"Community: {comm.name} ({comm.member_count}人)")

# ── 再加12条供需 ──
more_supplies = [
    {"type": 1, "title": "优质医疗器械渠道商寻合作", "desc": "三甲医院检验科主任，寻求精准检测设备渠道合作",
     "company": "瑞慈医疗集团", "tags": [4, 5], "price": "面议"},
    {"type": 1, "title": "品牌出海一站式服务", "desc": "提供亚马逊+独立站+TikTok全链路代运营",
     "company": "蓝鲸出海科技", "tags": [6, 7], "price": "按效果付费"},
    {"type": 2, "title": "寻求AI客服解决方案", "desc": "电商平台日均咨询量10万+，需大模型客服",
     "company": "杭州云谷电商", "tags": [1, 2], "price": "30-50万/年"},
    {"type": 1, "title": "芯片封装测试产能合作", "desc": "自有封装厂，月产能50kk，寻求设计公司订单",
     "company": "华芯封装（苏州）", "tags": [11, 12], "price": "有竞争力"},
    {"type": 2, "title": "寻找新能源商用车VC", "desc": "种子轮融资3000万，团队来自比亚迪/特斯拉",
     "company": "乾丰新能源科技", "tags": [9, 10], "price": "3000万/估值1.2亿"},
    {"type": 1, "title": "高净值客户理财需求", "desc": "服务500位千万资产客户，寻求优质固收产品",
     "company": "钜派财富管理", "tags": [8], "price": "年化8-12%"},
    {"type": 2, "title": "连锁餐饮数字化改造", "desc": "200家门店需POS+会员+供应链一体化系统",
     "company": "湘鄂情连锁", "tags": [2, 3], "price": "80-120万"},
    {"type": 1, "title": "政府产业基金寻GP", "desc": "50亿规模，引导基金需子基金管理人",
     "company": "深圳市引导基金", "tags": [8, 10], "price": "管理费1.5%/年"},
    {"type": 2, "title": "寻求消费品牌TP代运营", "desc": "年GMV 5亿天猫店，需专业TP提升ROI",
     "company": "完美宣言（广州）", "tags": [6, 7], "price": "销售额8-12%"},
    {"type": 1, "title": "碳中和园区招商", "desc": "上海周边2000亩绿电园区，优惠电价招商",
     "company": "临港绿能科技园", "tags": [9, 10], "price": "租金优惠"},
    {"type": 2, "title": "医疗器械临床试验CRO", "desc": "寻求靠谱CRO合作，III类器械注册",
     "company": "联影医疗科技", "tags": [4, 5], "price": "按项目结算"},
    {"type": 1, "title": "半导体设备融资租赁", "desc": "针对晶圆厂设备需求，提供融资租赁解决方案",
     "company": "芯鑫租赁", "tags": [11, 12], "price": "利率4-6%"},
]

my_profile = profiles[0]
for s in more_supplies:
    Supply.objects.create(
        profile=my_profile, title=s["title"], content=s["desc"],
        supply_type=s["type"], tags=s.get("tags", []),
    )
print(f"Supply: now {Supply.objects.count()} records")

# ── 丰富Profile数据 ──
for p in profiles:
    p.bio = f"毕业于{p.education_school or '某校'}，现任{p.position or '某职位'}。"
    p.save()
print("Profile bios updated")

print("\n✅ seed_pages 种子数据完成")
