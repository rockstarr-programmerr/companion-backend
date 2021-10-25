from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext as _
from rest_framework import serializers
from rest_framework.reverse import reverse

User = get_user_model()


USER_SERIALIZER_FIELDS = ['url', 'pk', 'nickname', 'email', 'avatar', 'avatar_thumbnail']

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

    def validate_email(self, email):
        if email and User.objects.filter(email=email).exists():
            raise serializers.ValidationError(
                _('A user with that email already exists.')
            )
        return email


class UserSearchSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['nickname', 'email', 'avatar_thumbnail']
        extra_kwargs = {
            'nickname': {'read_only': True},
            'email': {'read_only': True},
            'avatar_thumbnail': {'read_only': True},
        }

    def to_representation(self, instance):
        repr_ = super().to_representation(instance)
        if not repr_['avatar_thumbnail']:
            repr_['avatar_thumbnail'] = instance.social_avatar_url or None
        return repr_

class MyInfoSerializer(UserSerializer):
    event_invitations_url = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = USER_SERIALIZER_FIELDS + ['event_invitations_url']

    def get_event_invitations_url(self, user):
        request = self.context['request']
        return reverse('user-my-event-invitation-list', request=request)


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


class ResetPasswordSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    password = serializers.CharField(write_only=True, validators=[validate_password])


class EmailResetPasswordLinkTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['nickname', 'email', 'date_joined']
