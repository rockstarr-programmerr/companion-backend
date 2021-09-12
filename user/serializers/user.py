from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.reverse import reverse

from user.models import USERNAME_MIN_LENGTH

User = get_user_model()


USER_SERIALIZER_FIELDS = ['url', 'pk', 'username', 'email', 'avatar', 'avatar_thumbnail']

class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = USER_SERIALIZER_FIELDS
        extra_kwargs = {
            'url': {'read_only': True},
            'pk': {'read_only': True},
            'avatar': {'allow_null': True},
            'avatar_thumbnail': {'read_only': True},
        }

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if 'avatar' in attrs:
            attrs['avatar_thumbnail'] = attrs['avatar']
        return attrs

    def to_representation(self, instance):
        repr_ = super().to_representation(instance)
        if not repr_['avatar']:
            repr_['avatar'] = instance.social_avatar_url or None
            repr_['avatar_thumbnail'] = instance.social_avatar_url or None
        return repr_

    def save(self, **kwargs):
        if 'avatar' in self.validated_data and self.validated_data['avatar'] is None:
            kwargs['social_avatar_url'] = ''
        return super().save(**kwargs)


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'password']
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

class MyInfoSerializer(UserSerializer):
    event_invitations_url = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = USER_SERIALIZER_FIELDS + ['event_invitations_url']

    def get_event_invitations_url(self, user):
        request = self.context['request']
        return reverse('user-my-event-invitation-list', request=request)
