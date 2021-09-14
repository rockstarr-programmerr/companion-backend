from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from rest_framework import serializers
from rest_framework.generics import get_object_or_404

from split_the_bill.models import EventInvitation
from user.serializers.user import UserSearchSerializer

User = get_user_model()


class EventInvitationRequestSerializer(serializers.HyperlinkedModelSerializer):
    email = serializers.CharField(source='user.email')

    class Meta:
        model = EventInvitation
        fields = ['event', 'email']

    def to_representation(self, invitation):
        serializer = EventInvitationResponseSerializer(instance=invitation, context=self.context)
        return serializer.data

    def validate_email(self, email):
        if email == self.context['request'].user.email:
            raise serializers.ValidationError(
                _('You cannot invite yourself.')
            )
        if EventInvitation.objects.filter(user__email=email).exists():
            raise serializers.ValidationError(
                _('This user is already invited or is already a member.')
            )
        return email

    def create(self, validated_data):
        email = validated_data['user']['email']
        user = get_object_or_404(User, email=email)
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
