from django.contrib.auth.models import AbstractUser, UserManager
from django.core.validators import validate_image_file_extension
from django.db import models
from django.utils.translation import gettext_lazy as _
from PIL import Image

USERNAME_MIN_LENGTH = 3
AVATAR_WIDTH = 256
AVATAR_HEIGHT = 256
AVATAR_THUMBNAIL_WIDTH = 64
AVATAR_THUMBNAIL_HEIGHT = 64


def get_first_part_of_email(email):
    return email.split('@')[0]


class CustomUserManager(UserManager):
    """
    Customize to allow creating user with just email, no need username
    """
    def create_user(self, username=None, email=None, password=None, **extra_fields):
        assert bool(email), 'Email is required for creating user.'
        username = get_first_part_of_email(email)
        return super().create_user(username, email=email, password=password, **extra_fields)

    def create_superuser(self, username=None, email=None, password=None, **extra_fields):
        assert bool(email), 'Email is required for creating user.'
        username = get_first_part_of_email(email)
        return super().create_superuser(username, email=email, password=password, **extra_fields)


class User(AbstractUser):
    email = models.EmailField(
        _('email address'),
        unique=True,
        error_messages={
            'unique': _("A user with that email already exists."),
        },
    )
    nickname = models.CharField(
        _('nickname'),
        max_length=150,
    )
    username = models.CharField(
        _('username'),
        max_length=150,
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

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return f'{self.nickname} - {self.email}'

    def save(self, *args, **kwargs):
        self.set_default_nickname()
        super().save(*args, **kwargs)
        self._make_thumbnail(self.avatar, AVATAR_WIDTH, AVATAR_HEIGHT)
        self._make_thumbnail(self.avatar_thumbnail, AVATAR_THUMBNAIL_WIDTH, AVATAR_THUMBNAIL_HEIGHT)

    def set_default_nickname(self):
        if not self.nickname:
            self.nickname = get_first_part_of_email(self.email)

    @staticmethod
    def _make_thumbnail(image, width, height):
        if image and (
            image.width > width or
            image.height > height
        ):
            with Image.open(image.path) as f:
                f.thumbnail((width, height))
                f.save(image.path)
