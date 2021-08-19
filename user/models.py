from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    username = models.CharField(
        _('username'),
        max_length=150,
        unique=True,
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )
