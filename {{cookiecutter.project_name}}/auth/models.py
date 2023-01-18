from datetime import datetime
from django.db import models
from django.utils.encoding import smart_str
from django.contrib.auth.models import AbstractUser, Group as DjangoGroup


class Group(DjangoGroup):
    group_id = models.CharField("ID", primary_key=True, max_length=8)
    name = models.CharField("组名称", max_length=150, unique=True)

    class Meta:
        db_table = "groups"
        verbose_name = "用户组"
        verbose_name_plural = verbose_name


class User(AbstractUser):
    user_id = models.CharField("ID", primary_key=True, max_length=8)
    username = models.CharField("用户名", max_length=64, unique=True)
    nickname = models.CharField("昵称", max_length=24)
    avatar = models.FileField("头像", upload_to="avatar", null=True, blank=True)
    sex = models.IntegerField("性别", choices=((0, "未知"), (1, "男"), (2, "女")), default=0)
    description = models.CharField("描述", max_length=32, null=True, blank=True)
    phone = models.CharField("手机号", max_length=24, null=True, blank=True)
    email = models.CharField("电子邮箱", max_length=64)
    is_superuser = models.BooleanField("管理员", default=False)

    class Meta:
        db_table = "users"
        verbose_name = "用户"
        verbose_name_plural = verbose_name

    def __str__(self):
        return smart_str("%s-%s" % (self.username, self.nickname))

    def update_last_login(self):
        self.last_login = datetime.now()
        self.save()
