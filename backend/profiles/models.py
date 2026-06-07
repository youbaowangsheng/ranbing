import uuid as uuid_lib
from django.db import models
from django.conf import settings


class Tag(models.Model):
    """标签表 L1~L5五层"""
    L1_CHOICES = [
        ('供给资源', '供给资源'),
        ('需求帮助', '需求帮助'),
        ('行业经验', '行业经验'),
        ('投资意向', '投资意向'),
        ('社交兴趣', '社交兴趣'),
    ]
    TAG_TYPE_CHOICES = [(1, '供给'), (2, '需求'), (3, '通用')]

    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=64)
    l1_category = models.CharField(max_length=32, choices=L1_CHOICES)
    l2_group = models.CharField(max_length=32, blank=True, default='')
    l3_item = models.CharField(max_length=64, blank=True, default='')
    l4_attr = models.CharField(max_length=64, blank=True, default='')
    l5_detail = models.CharField(max_length=64, blank=True, default='')
    tag_type = models.SmallIntegerField(choices=TAG_TYPE_CHOICES, default=3)
    is_recommend = models.BooleanField(default=False)
    hot_score = models.IntegerField(default=0)

    class Meta:
        db_table = 'tags'
        ordering = ['-hot_score']

    def __str__(self):
        return self.name


class Profile(models.Model):
    """校友档案表"""
    CERT_LEVEL_CHOICES = [(0, '未认证'), (1, '手机认证'), (2, '校友认证'), (3, '深度认证')]
    GENDER_CHOICES = [(0, '未知'), (1, '男'), (2, '女')]

    id = models.BigAutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid_lib.uuid4, unique=True, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    real_name = models.CharField(max_length=64)
    gender = models.SmallIntegerField(choices=GENDER_CHOICES, default=0)
    birthday = models.DateField(null=True, blank=True)
    company = models.CharField(max_length=128, blank=True, default='')
    position = models.CharField(max_length=128, blank=True, default='')
    industry = models.CharField(max_length=64, blank=True, default='')
    city = models.CharField(max_length=64, blank=True, default='')
    avatar = models.ImageField(upload_to='avatars/', blank=True, default='')
    bio = models.TextField(blank=True, default='')
    education_year = models.CharField(max_length=10, blank=True, default='')  # e.g. "2015"
    education_major = models.CharField(max_length=128, blank=True, default='')
    education_school = models.CharField(max_length=128, blank=True, default='')
    cert_level = models.SmallIntegerField(choices=CERT_LEVEL_CHOICES, default=0)
    cert_status = models.SmallIntegerField(default=0)  # 0=未提交 1=审核中 2=通过 3=拒绝
    cert_document_url = models.URLField(max_length=512, blank=True, default='')
    conn_count = models.IntegerField(default=0)
    active_score = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    last_active_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'profiles'

    def __str__(self):
        return f'{self.real_name}@{self.company}'


class ProfileTag(models.Model):
    """用户-标签关联表"""
    TAG_TYPE_CHOICES = [(1, '供给标签'), (2, '需求标签')]

    id = models.BigAutoField(primary_key=True)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='profile_tags')
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    tag_type = models.SmallIntegerField(choices=TAG_TYPE_CHOICES)  # 1=供给 2=需求
    weight = models.DecimalField(max_digits=3, decimal_places=2, default=1.0)
    is_ai_ext = models.BooleanField(default=False)  # AI推荐添加

    class Meta:
        db_table = 'profile_tags'
        unique_together = ('profile', 'tag')

    def __str__(self):
        return f'{self.profile_id}-{self.tag.name}'


class ProfileEmbedding(models.Model):
    """用户向量表（pgvector）"""
    id = models.BigAutoField(primary_key=True)
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='embedding')
    # embedding 字段在PostgreSQL中会是Vector(1536)，Django中用JSONField暂存，迁移后手动ALTER
    embedding = models.JSONField(default=list)
    model_name = models.CharField(max_length=64, default='text-embedding-3-small')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'profile_embeddings'

    def __str__(self):
        return f'embedding:{self.profile_id}'


class PrivateMessage(models.Model):
    """用户间私信表"""
    id = models.BigAutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid_lib.uuid4, unique=True, editable=False)
    from_profile = models.ForeignKey(
        'Profile', on_delete=models.CASCADE, related_name='messages_sent'
    )
    to_profile = models.ForeignKey(
        'Profile', on_delete=models.CASCADE, related_name='messages_received'
    )
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'private_messages'
        ordering = ['created_at']

    def __str__(self):
        return f'PM:{self.from_profile_id}->{self.to_profile_id}'
