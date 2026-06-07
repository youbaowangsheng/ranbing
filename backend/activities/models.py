import uuid as uuid_lib
from django.db import models


class Activity(models.Model):
    """社交活动表"""
    TYPE_CHOICES = [
        (1, '沙龙'), (2, '路演'), (3, '培训班'),
        (4, '社交聚会'), (5, '线上讲座')
    ]
    ENROLL_MODE_CHOICES = [(1, '免费'), (2, '付费'), (3, '审核')]
    STATUS_CHOICES = [(1, '报名中'), (2, '进行中'), (3, '已结束'), (4, '已取消')]
    AUDIT_STATUS_CHOICES = [(0, '待审核'), (1, '审核通过'), (2, '审核拒绝')]

    id = models.BigAutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid_lib.uuid4, unique=True, editable=False)
    title = models.CharField(max_length=256)
    description = models.TextField(blank=True, default='')
    cover_url = models.URLField(max_length=512, blank=True, default='')
    activity_type = models.SmallIntegerField(choices=TYPE_CHOICES)
    organizer = models.ForeignKey('profiles.Profile', on_delete=models.CASCADE, related_name='organized_activities')
    host_school = models.CharField(max_length=128, blank=True, default='')
    location = models.CharField(max_length=256, blank=True, default='')
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    max_attendees = models.IntegerField(null=True, blank=True)
    current_attendees = models.IntegerField(default=0)
    enrollment_mode = models.SmallIntegerField(choices=ENROLL_MODE_CHOICES, default=1)
    fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tags = models.JSONField(default=list)
    status = models.SmallIntegerField(choices=STATUS_CHOICES, default=1)
    audit_status = models.SmallIntegerField(choices=AUDIT_STATUS_CHOICES, default=0)
    audit_time = models.DateTimeField(null=True, blank=True)
    audit_comment = models.CharField(max_length=256, blank=True, default='')
    ai_match_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'activities'
        ordering = ['-start_time']

    def __str__(self):
        return self.title


class ActivityEnrollment(models.Model):
    """活动报名表"""
    STATUS_CHOICES = [
        (1, '已报名'), (2, '已确认'), (3, '已取消'), (4, '已签到')
    ]

    id = models.BigAutoField(primary_key=True)
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='enrollments')
    profile = models.ForeignKey('profiles.Profile', on_delete=models.CASCADE, related_name='enrollments')
    enrollment_status = models.SmallIntegerField(choices=STATUS_CHOICES, default=1)
    ai_recommended = models.BooleanField(default=False)
    ai_match_score = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'activity_enrollments'
        unique_together = ('activity', 'profile')

    def __str__(self):
        return f'{self.profile_id}@{self.activity_id}'
