from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext as _
from rest_framework import serializers

from user.models import USERNAME_MIN_LENGTH

User = get_user_model()


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'pk', 'username', 'email', 'avatar']
        extra_kwargs = {
            'url': {'read_only': True},
            'pk': {'read_only': True},
        }


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        extra_kwargs = {
            'password': {
                'write_only': True,
                'validators': [validate_password]
            }
        }

    def validate_email(self, email):
        if email and User.objects.filter(email=email).exists():
            raise serializers.ValidationError(
                _('A user with this email already exists.')
            )
        return email


class UserSearchSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['username']
        extra_kwargs = {
            'username': {
                'min_length': USERNAME_MIN_LENGTH,
            }
        }


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])


class EmailResetPasswordLinkSerializer(serializers.Serializer):
    deeplink = serializers.CharField()
    email = serializers.EmailField()

    def validate_deeplink(self, link):
        if link not in settings.ALLOWED_DEEPLINKS:
            raise serializers.ValidationError(
                _('This deeplink is not allowed.')
            )
        return link
