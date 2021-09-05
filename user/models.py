from django.contrib.auth.models import AbstractUser
from django.core.validators import (MinLengthValidator,
                                    validate_image_file_extension)
from django.db import models
from django.utils.translation import gettext_lazy as _
from PIL import Image

USERNAME_MIN_LENGTH = 3
AVATAR_WIDTH = 64
AVATAR_HEIGHT = 64

class User(AbstractUser):
    username = models.CharField(
        _('username'),
        max_length=150,
        unique=True,
        error_messages={
            'unique': _("A user with that username already exists."),
        },
        validators=[MinLengthValidator(USERNAME_MIN_LENGTH)],
    )
    avatar = models.ImageField(
        _('avatar'),
        upload_to='users/avatar/%Y/%m',
        blank=True,
        validators=[validate_image_file_extension],
    )

    def __str__(self):
        text = self.username
        if self.email:
            text += f' - {self.email}'
        return text

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.avatar and (
            self.avatar.width > AVATAR_WIDTH or
            self.avatar.height > AVATAR_HEIGHT
        ):
            with Image.open(self.avatar.path) as img:
                img.thumbnail((AVATAR_WIDTH, AVATAR_HEIGHT))
                img.save(self.avatar.path)

    @classmethod
    def get_user_by_email(cls, email):
        return cls.objects.filter(email=email).first()
