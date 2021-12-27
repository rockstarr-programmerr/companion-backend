from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.reverse import reverse

from split_the_bill.models import Event, EventInvitation

User = get_user_model()


class _EventCreatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['nickname', 'email', 'avatar', 'avatar_thumbnail']


class _EventSerializer(serializers.ModelSerializer):
    creator = _EventCreatorSerializer()

    class Meta:
        model = Event
        fields = ['pk', 'name', 'creator']



class UserEventInvitationSerializer(serializers.HyperlinkedModelSerializer):
    event = _EventSerializer(read_only=True)
    accept_invitation_url = serializers.SerializerMethodField()
    decline_invitation_url = serializers.SerializerMethodField()

    class Meta:
        model = EventInvitation
        fields = [
            'url', 'pk', 'event', 'status',
            'create_time', 'update_time',
            'accept_invitation_url', 'decline_invitation_url',
        ]
        extra_kwargs = {
            'url': {'view_name': 'user-my-event-invitation-detail'},
            'status': {'read_only': True}
        }

    def get_accept_invitation_url(self, invitation):
        request = self.context['request']
        return reverse('user-my-event-invitation-accept', kwargs={'pk': invitation.pk}, request=request)

    def get_decline_invitation_url(self, invitation):
        request = self.context['request']
        return reverse('user-my-event-invitation-decline', kwargs={'pk': invitation.pk}, request=request)
