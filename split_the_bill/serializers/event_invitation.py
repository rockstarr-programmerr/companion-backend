from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from rest_framework import serializers
from rest_framework.generics import get_object_or_404

from split_the_bill.models import EventInvitation
from user.serializers.user import UserSearchSerializer

User = get_user_model()


class EventInvitationRequestSerializer(serializers.HyperlinkedModelSerializer):
    username = serializers.CharField(source='user.username')

    class Meta:
        model = EventInvitation
        fields = ['event', 'username']

    def to_representation(self, invitation):
        serializer = EventInvitationResponseSerializer(instance=invitation, context=self.context)
        return serializer.data

    def validate_username(self, username):
        if username == self.context['request'].user.username:
            raise serializers.ValidationError(
                _('You cannot invite yourself.')
            )
        if EventInvitation.objects.filter(user__username=username).exists():
            raise serializers.ValidationError(
                _('This user is already invited or is already a member.')
            )
        return username

    def create(self, validated_data):
        username = validated_data['user']['username']
        user = get_object_or_404(User, username=username)
        validated_data['user'] = user
        return super().create(validated_data)


class EventInvitationResponseSerializer(serializers.HyperlinkedModelSerializer):
    user = UserSearchSerializer()

    class Meta:
        model = EventInvitation
        fields = ['url', 'pk', 'event', 'user', 'status', 'create_time', 'update_time']
        extra_kwargs = {
            'url': {'view_name': 'event-invitation-detail'}
        }
