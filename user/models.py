from django.contrib.auth.models import AbstractUser
from django.core.validators import (MinLengthValidator,
                                    validate_image_file_extension)
from django.db import models
from django.utils.translation import gettext_lazy as _
from PIL import Image

USERNAME_MIN_LENGTH = 3
AVATAR_WIDTH = 256
AVATAR_HEIGHT = 256
AVATAR_THUMBNAIL_WIDTH = 64
AVATAR_THUMBNAIL_HEIGHT = 64

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
        upload_to='users/avatar/%Y/%m',
        blank=True,
        validators=[validate_image_file_extension]
    )
    avatar_thumbnail = models.ImageField(
        upload_to='users/avatar_thumbnail/%Y/%m',
        blank=True,
        validators=[validate_image_file_extension]
    )
    social_avatar_url = models.URLField(blank=True)

    def __str__(self):
        text = self.username
        if self.email:
            text += f' - {self.email}'
        return text

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self._make_thumbnail(self.avatar, AVATAR_WIDTH, AVATAR_HEIGHT)
        self._make_thumbnail(self.avatar_thumbnail, AVATAR_THUMBNAIL_WIDTH, AVATAR_THUMBNAIL_HEIGHT)

    @staticmethod
    def _make_thumbnail(image, width, height):
        if image and (
            image.width > width or
            image.height > height
        ):
            with Image.open(image.path) as f:
                f.thumbnail((width, height))
                f.save(image.path)
