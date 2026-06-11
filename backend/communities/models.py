import uuid as uuid_lib
from django.db import models


class Community(models.Model):
    """校友社群表"""
    TYPE_CHOICES = [
        (1, '行业社群'), (2, '地域社群'), (3, '校友群'), (4, '兴趣社群')
    ]
    STATUS_CHOICES = [(1, '公开'), (2, '私密'), (3, '已解散')]

    id = models.BigAutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid_lib.uuid4, unique=True, editable=False)
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True, default='')
    community_type = models.SmallIntegerField(choices=TYPE_CHOICES)
    school = models.CharField(max_length=128, blank=True, default='')
    cover_url = models.URLField(max_length=512, blank=True, default='')
    member_count = models.IntegerField(default=0)
    owner = models.ForeignKey('profiles.Profile', on_delete=models.CASCADE, related_name='owned_communities')
    status = models.SmallIntegerField(choices=STATUS_CHOICES, default=1)
    qr_code_url = models.URLField(max_length=512, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'communities'

    def __str__(self):
        return self.name


class CommunityMember(models.Model):
    """社群成员表"""
    ROLE_CHOICES = [(1, '普通成员'), (2, '管理员'), (3, '群主')]
    STATUS_CHOICES = [(1, '正常'), (2, '已退出'), (3, '已移除')]

    id = models.BigAutoField(primary_key=True)
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='members')
    profile = models.ForeignKey('profiles.Profile', on_delete=models.CASCADE, related_name='community_memberships')
    role = models.SmallIntegerField(choices=ROLE_CHOICES, default=1)
    status = models.SmallIntegerField(choices=STATUS_CHOICES, default=1)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'community_members'
        unique_together = ('community', 'profile')

    def __str__(self):
        return f'{self.profile_id} in {self.community_id}'


class Message(models.Model):
    """社群消息表（App内主动发布的内容）"""
    TYPE_CHOICES = [(1, '文本'), (2, '图片'), (3, '链接'), (4, '小程序')]
    AI_SIGNAL_CHOICES = [
        (1, '供需信号'), (2, '问答信号'), (3, '合作意向'), (4, '资源推介')
    ]
    AUDIT_STATUS_CHOICES = [(0, '待审核'), (1, '审核通过'), (2, '审核拒绝')]

    id = models.BigAutoField(primary_key=True)
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='messages')
    profile = models.ForeignKey('profiles.Profile', on_delete=models.CASCADE, related_name='messages')
    content = models.TextField()
    msg_type = models.SmallIntegerField(choices=TYPE_CHOICES, default=1)
    is_pinned = models.BooleanField(default=False)
    like_count = models.IntegerField(default=0)
    ai_signal_type = models.SmallIntegerField(choices=AI_SIGNAL_CHOICES, null=True, blank=True)
    ai_signal_extracted = models.BooleanField(default=False)
    audit_status = models.SmallIntegerField(choices=AUDIT_STATUS_CHOICES, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'messages'
        ordering = ['-created_at']

    def __str__(self):
        return f'msg:{self.id} in {self.community_id}'
