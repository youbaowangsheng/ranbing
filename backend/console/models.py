from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    PLAN_CHOICES = [
        ('free', '免费版'),
        ('pro', '专业版'),
        ('enterprise', '企业版'),
    ]
    USER_TYPE_CHOICES = [
        ('admin', '管理员'),
        ('superuser', '超级用户'),
        ('regular', '普通用户'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='console_profile')
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='regular', verbose_name='用户类型')
    phone = models.CharField(max_length=20, blank=True, verbose_name='手机号')
    company = models.CharField(max_length=200, blank=True, verbose_name='公司')
    industry = models.CharField(max_length=100, blank=True, verbose_name='行业')
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='free', verbose_name='套餐')
    max_agents = models.IntegerField(default=3, verbose_name='最大Agent数')
    token_quota = models.BigIntegerField(default=100000, verbose_name='Token配额')
    token_used = models.BigIntegerField(default=0, verbose_name='已用Token')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'console_user_profile'
        verbose_name = '用户扩展信息'

    def __str__(self):
        return f'{self.user.username} - {self.company}'


class AgentConfig(models.Model):
    AGENT_TYPE_CHOICES = [
        ('community', '社群助手'),
        ('matching', '匹配助手'),
        ('publish', '发布助手'),
        ('supply_demand', '供需助手'),
        ('network', '人脉助手'),
        ('event', '活动助手'),
        ('custom', '自定义'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='agent_configs', verbose_name='用户')
    fipai_agent_id = models.IntegerField(null=True, blank=True, verbose_name='FIPAI Agent ID')
    agent_name = models.CharField(max_length=200, verbose_name='Agent名称')
    agent_type = models.CharField(max_length=50, choices=AGENT_TYPE_CHOICES, default='custom', verbose_name='Agent类型')
    description = models.TextField(blank=True, verbose_name='描述')
    capabilities = models.JSONField(default=list, verbose_name='能力列表')
    config = models.JSONField(default=dict, verbose_name='业务配置')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'console_agent_config'
        verbose_name = 'Agent业务配置'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} - {self.agent_name}'


class UsageRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='usage_records', verbose_name='用户')
    agent = models.ForeignKey(AgentConfig, on_delete=models.SET_NULL, null=True, related_name='usage_records', verbose_name='Agent')
    tokens = models.BigIntegerField(default=0, verbose_name='Token消耗')
    cost = models.DecimalField(max_digits=10, decimal_places=4, default=0, verbose_name='费用')
    request_count = models.IntegerField(default=0, verbose_name='请求次数')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'console_usage_record'
        verbose_name = '用量记录'
        ordering = ['-created_at']


class MatchingRecord(models.Model):
    STATUS_CHOICES = [
        ('pending', '待匹配'),
        ('matched', '已匹配'),
        ('confirmed', '已确认'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='matching_records', verbose_name='用户')
    agent = models.ForeignKey(AgentConfig, on_delete=models.SET_NULL, null=True, verbose_name='Agent')
    demand_id = models.CharField(max_length=100, blank=True, verbose_name='需求ID')
    supply_id = models.CharField(max_length=100, blank=True, verbose_name='供给ID')
    match_score = models.FloatField(default=0, verbose_name='匹配分数')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='状态')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'console_matching_record'
        verbose_name = '匹配记录'
        ordering = ['-created_at']


class PublishTask(models.Model):
    STATUS_CHOICES = [
        ('pending', '待发布'),
        ('published', '已发布'),
        ('failed', '发布失败'),
        ('cancelled', '已取消'),
    ]

    PLATFORM_CHOICES = [
        ('wechat', '微信'),
        ('weibo', '微博'),
        ('dingtalk', '钉钉'),
        ('feishu', '飞书'),
        ('custom', '自定义'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='publish_tasks', verbose_name='用户')
    agent = models.ForeignKey(AgentConfig, on_delete=models.SET_NULL, null=True, verbose_name='Agent')
    title = models.CharField(max_length=200, verbose_name='标题')
    content = models.TextField(verbose_name='内容')
    platform = models.CharField(max_length=50, choices=PLATFORM_CHOICES, default='custom', verbose_name='发布平台')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='状态')
    published_at = models.DateTimeField(null=True, blank=True, verbose_name='发布时间')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'console_publish_task'
        verbose_name = '发布任务'
        ordering = ['-created_at']
