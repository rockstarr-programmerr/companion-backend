from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from companion.utils.serializers import ExtraDetailActionUrlsMixin
from user.models import USERNAME_MIN_LENGTH

User = get_user_model()


class UserSerializer(ExtraDetailActionUrlsMixin, serializers.HyperlinkedModelSerializer):
    extra_action_urls = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ['url', 'pk', 'username', 'email', 'avatar', 'extra_action_urls']


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


class UserSearchSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['username']
        extra_kwargs = {
            'username': {
                'min_length': USERNAME_MIN_LENGTH,
            }
        }
