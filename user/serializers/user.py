from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from user.models import USERNAME_MIN_LENGTH

User = get_user_model()


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'pk', 'username', 'email', 'avatar', 'avatar_thumbnail']
        extra_kwargs = {
            'url': {'read_only': True},
            'pk': {'read_only': True},
            'avatar': {'allow_null': True},
            'avatar_thumbnail': {'read_only': True},
        }

    def validate(self, attrs):
        if 'avatar' in attrs:
            attrs['avatar_thumbnail'] = attrs['avatar']
        return attrs


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
        fields = ['username', 'avatar_thumbnail']
        extra_kwargs = {
            'username': {
                'min_length': USERNAME_MIN_LENGTH,
            },
            'avatar_thumbnail': {
                'read_only': True,
            }
        }
