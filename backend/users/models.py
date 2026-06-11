import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager


class UserManager(BaseUserManager):
    def create_user(self, phone=None, password=None, nickname='', **extra_fields):
        if not phone and not extra_fields.get('email'):
            raise ValueError('手机号或邮箱不能同时为空')
        user = self.model(phone=phone, nickname=nickname, **extra_fields)
        if password:
            user.set_password(password)  # Django 加密存储
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_user_with_phone(self, phone, password=None, real_name='', nickname=''):
        """创建用户（手机已验证）"""
        return self.create_user(
            phone=phone,
            password=password,
            nickname=nickname or f"用户{phone[-4:]}",
            is_phone_verified=True,
            real_name=real_name,
        )

    def get_by_phone(self, phone):
        return self.get(phone=phone)


class User(AbstractBaseUser):
    """用户表：微信openid/手机号的容器"""
    id = models.BigAutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    phone = models.CharField(max_length=20, unique=True, null=True, blank=True)
    email = models.CharField(max_length=128, unique=True, null=True, blank=True, verbose_name='邮箱')
    wx_openid = models.CharField(max_length=128, unique=True, null=True, blank=True)
    wx_unionid = models.CharField(max_length=128, unique=True, null=True, blank=True)
    nickname = models.CharField(max_length=64, blank=True, default='')
    real_name = models.CharField(max_length=32, blank=True, default='', verbose_name='真实姓名')
    avatar_url = models.URLField(max_length=512, blank=True, default='')
    status = models.SmallIntegerField(default=1)  # 1=正常 2=封禁 9=注销
    is_verified = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False, verbose_name='手机已验证')
    sms_code_fail_count = models.IntegerField(default=0, verbose_name='验证码失败次数')
    last_login_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []

    class Meta:
        db_table = 'users'

    def __str__(self):
        return f'{self.nickname or self.phone}'
