import uuid as uuid_lib
from django.db import models
from django.conf import settings


class Supply(models.Model):
    """供需表"""
    TYPE_CHOICES = [(1, '供给'), (2, '需求')]
    STATUS_CHOICES = [(1, '有效'), (2, '已下架'), (3, '已成交')]
    AUDIT_STATUS_CHOICES = [(0, '待审核'), (1, '审核通过'), (2, '审核拒绝')]

    id = models.BigAutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid_lib.uuid4, unique=True, editable=False)
    profile = models.ForeignKey('profiles.Profile', on_delete=models.CASCADE, related_name='supplies')
    supply_type = models.SmallIntegerField(choices=TYPE_CHOICES)
    title = models.CharField(max_length=256)
    content = models.TextField(blank=True, default='')
    tags = models.JSONField(default=list)  # [tag_id, ...]
    match_count = models.IntegerField(default=0)
    is_anonymous = models.BooleanField(default=False)
    view_count = models.IntegerField(default=0)
    status = models.SmallIntegerField(choices=STATUS_CHOICES, default=1)
    audit_status = models.SmallIntegerField(choices=AUDIT_STATUS_CHOICES, default=0)
    audit_time = models.DateTimeField(null=True, blank=True)
    quality_score = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'supplies'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_supply_type_display()}:{self.title}'


class SupplyEmbedding(models.Model):
    """供需向量表"""
    id = models.BigAutoField(primary_key=True)
    supply = models.OneToOneField(Supply, on_delete=models.CASCADE, related_name='embedding')
    embedding = models.JSONField(default=list)
    model_name = models.CharField(max_length=64, default='text-embedding-3-small')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'supply_embeddings'


class Match(models.Model):
    """AI匹配记录表"""
    TYPE_CHOICES = [(1, '供需匹配'), (2, '人脉推荐'), (3, '活动推荐')]
    STATUS_CHOICES = [(1, '待处理'), (2, '已联系'), (3, '已成交'), (4, '已忽略')]
    PUSH_CHOICES = [(0, '未推送'), (1, '已推送'), (2, '已点击'), (3, '已反馈')]
    FEEDBACK_CHOICES = [(1, '准确'), (2, '一般'), (3, '不匹配')]

    id = models.BigAutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid_lib.uuid4, unique=True, editable=False)
    supply = models.ForeignKey(Supply, on_delete=models.CASCADE, related_name='matches')
    target_profile = models.ForeignKey('profiles.Profile', on_delete=models.CASCADE, related_name='received_matches')
    match_score = models.DecimalField(max_digits=5, decimal_places=4)
    ai_reason = models.TextField(blank=True, default='')
    match_type = models.SmallIntegerField(choices=TYPE_CHOICES)
    status = models.SmallIntegerField(choices=STATUS_CHOICES, default=1)
    push_status = models.SmallIntegerField(choices=PUSH_CHOICES, default=0)
    feedback_score = models.SmallIntegerField(choices=FEEDBACK_CHOICES, null=True, blank=True)
    feedback_text = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'matches'
        unique_together = ('supply', 'target_profile', 'match_type')
        ordering = ['-match_score']

    def __str__(self):
        return f'match:{self.id} score:{self.match_score}'


class Connection(models.Model):
    """关系链表"""
    TYPE_CHOICES = [
        (1, '好友'), (2, '粉丝'), (3, '校友'),
        (4, '活动认识'), (5, '供需认识')
    ]
    STATUS_CHOICES = [(1, '有效'), (2, '已删除')]

    id = models.BigAutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid_lib.uuid4, unique=True, editable=False)
    user_a = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='connections_from')
    user_b = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='connections_to')
    conn_type = models.SmallIntegerField(choices=TYPE_CHOICES)
    relation_strength = models.DecimalField(max_digits=4, decimal_places=2, default=0.5)
    last_interact_at = models.DateTimeField(null=True, blank=True)
    interact_count = models.IntegerField(default=0)
    is_mutual = models.BooleanField(default=False)
    status = models.SmallIntegerField(choices=STATUS_CHOICES, default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'connections'
        ordering = ['-relation_strength']

    def save(self, *args, **kwargs):
        # 保证 user_a_id < user_b_id
        if self.user_a_id > self.user_b_id:
            self.user_a_id, self.user_b_id = self.user_b_id, self.user_a_id
        super().save(*args, **kwargs)

    def __str__(self):
        return f'conn:{self.user_a_id}-{self.user_b_id}'


class Followup(models.Model):
    """AI跟进记录表"""
    TRIGGER_CHOICES = [
        (1, '刚匹配'), (2, '活动结束'), (3, '社群互动'), (4, '自定义')
    ]
    TYPE_CHOICES = [
        (1, 'AI建议'), (2, '已发送'), (3, '已回复'), (4, '已添加微信')
    ]
    STATUS_CHOICES = [(0, 'pending'), (1, '已计划'), (2, '已发送'), (3, '已完成')]
    RESULT_CHOICES = [(1, 'positive'), (2, 'neutral'), (3, 'negative')]

    id = models.BigAutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid_lib.uuid4, unique=True, editable=False)
    from_profile = models.ForeignKey('profiles.Profile', on_delete=models.CASCADE, related_name='followups_from')
    to_profile = models.ForeignKey('profiles.Profile', on_delete=models.CASCADE, related_name='followups_to')
    trigger_event = models.SmallIntegerField(choices=TRIGGER_CHOICES)
    ai_script = models.TextField(blank=True, default='')
    followup_type = models.SmallIntegerField(choices=TYPE_CHOICES, default=1)
    scheduled_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    replied_at = models.DateTimeField(null=True, blank=True)
    result = models.SmallIntegerField(choices=RESULT_CHOICES, null=True, blank=True)
    result_text = models.TextField(blank=True, default='')
    status = models.SmallIntegerField(choices=STATUS_CHOICES, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'followups'
        ordering = ['-scheduled_at']

    def __str__(self):
        return f'followup:{self.id} from:{self.from_profile_id} to:{self.to_profile_id}'


class FriendRequest(models.Model):
    """加好友请求表"""
    STATUS_CHOICES = [(1, '待接受'), (2, '已接受'), (3, '已拒绝'), (4, '已过期')]

    id = models.BigAutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid_lib.uuid4, unique=True, editable=False)
    from_profile = models.ForeignKey(
        'profiles.Profile', on_delete=models.CASCADE, related_name='friend_requests_sent'
    )
    to_profile = models.ForeignKey(
        'profiles.Profile', on_delete=models.CASCADE, related_name='friend_requests_received'
    )
    # 可选：发起时可以附一句自我介绍/留言
    message = models.TextField(blank=True, default='')
    status = models.SmallIntegerField(choices=STATUS_CHOICES, default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'friend_requests'
        ordering = ['-created_at']
        unique_together = ('from_profile', 'to_profile')

    def __str__(self):
        return f'FriendRequest:{self.from_profile_id}->{self.to_profile_id}[{self.status}]'


class Card(models.Model):
    """电子名片表"""
    STATUS_CHOICES = [(1, '有效'), (2, '已禁用')]

    id = models.BigAutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid_lib.uuid4, unique=True, editable=False)
    owner = models.OneToOneField('profiles.Profile', on_delete=models.CASCADE, related_name='card')
    title = models.CharField(max_length=128, blank=True, default='')
    bio = models.TextField(blank=True, default='')
    show_company = models.BooleanField(default=True)
    show_position = models.BooleanField(default=True)
    show_education = models.BooleanField(default=True)
    show_tags = models.BooleanField(default=True)
    show_contact = models.BooleanField(default=True)
    style_config = models.JSONField(default=dict)  # 自定义样式配置
    view_count = models.IntegerField(default=0)
    status = models.SmallIntegerField(choices=STATUS_CHOICES, default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cards'

    def __str__(self):
        return f'Card:{self.owner_id}'
