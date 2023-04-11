from datetime import datetime
from django.db import models
from django.utils.encoding import smart_str
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractUser, Group as DjangoGroup
from model_utils.fields import StatusField
from model_utils.managers import QueryManager
from model_utils import Choices


class Group(DjangoGroup):
    query = QueryManager()

    class Meta:
        db_table = "groups"
        verbose_name = _("Group")
        verbose_name_plural = verbose_name


class User(AbstractUser):
    SEX_CHOICES = Choices(
        (0, _("Default")), (1, _("Male")), (2, _("Female"))
    )  # Perhaps more choices in your country?
    username = models.CharField(_("UserName"), max_length=64, unique=True)
    name = models.CharField(_("Name"), max_length=24)
    avatar = models.FileField(_("Avatar"), upload_to="avatar", null=True, blank=True)
    sex = StatusField(_("Sex"), choices_name="SEX_CHOICES", default=0)
    description = models.CharField(
        _("Description"), max_length=32, null=True, blank=True
    )
    phone = models.CharField(_("PhoneNumber"), max_length=24, null=True, blank=True)
    email = models.CharField(_("Email"), max_length=64, null=True, blank=True)
    is_superuser = models.BooleanField(_("IsSuperUser"), default=False)

    query = QueryManager()

    REQUIRED_FIELDS = []

    class Meta:
        db_table = "users"
        verbose_name = _("User")
        verbose_name_plural = verbose_name

    def __str__(self):
        return smart_str("%s-%s" % (self.username, self.name))

    def update_last_login(self):
        self.last_login = datetime.now()
        self.save()
