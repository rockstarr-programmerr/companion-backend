from django.utils.translation import gettext as _
from rest_framework import serializers
from rest_framework.fields import ListField
from rest_framework.reverse import reverse

from split_the_bill.models import Event, EventInvitation
from split_the_bill.utils.url import update_url_params
from user.serializers.user import UserSerializer

from ._common import PkField


class EventSerializer(serializers.HyperlinkedModelSerializer):
    creator = UserSerializer(read_only=True)
    members = UserSerializer(many=True, read_only=True)
    transactions_url = serializers.SerializerMethodField(read_only=True)
    invitations_url = serializers.SerializerMethodField(read_only=True)
    extra_action_urls = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Event
        fields = [
            'url', 'pk', 'name',
            'creator', 'members', 'create_time',
            'transactions_url', 'invitations_url', 'extra_action_urls',
        ]

    def get_transactions_url(self, event):
        url = reverse('transaction-list', request=self.context['request'])
        params = {'event': event.pk}
        return update_url_params(url, params)

    def get_invitations_url(self, event):
        url = reverse('event-invitation-list', request=self.context['request'])
        params = {'event': event.pk}
        return update_url_params(url, params)

    def get_extra_action_urls(self, transaction):
        kwargs = {
            'kwargs': {'pk': transaction.pk},
            'request': self.context['request'],
        }
        return {
            'invite_members': reverse('event-invite-members', **kwargs),
            'cancel_invite_members': reverse('event-cancel-invite-members', **kwargs),
            'remove_members': reverse('event-remove-members', **kwargs),
        }


class _EventMembersSerializer(serializers.Serializer):
    def __init__(self, *args, **kwargs):
        event = None
        if 'event' in kwargs:
            event = kwargs.pop('event')

        super().__init__(*args, **kwargs)

        assert not hasattr(self, 'event'), 'Serializer already has attribute `event`.'
        self.event = event


class InviteMembersSerializer(_EventMembersSerializer):
    member_usernames = ListField(child=serializers.CharField(), allow_empty=False, max_length=100)

    def validate_member_usernames(self, usernames):
        self._validate_alread_invited(usernames)
        self._validate_invite_creator(usernames)
        return usernames

    def _validate_alread_invited(self, usernames):
        invited_users = self.event.invited_users.all()
        invited_usernames = [user.username for user in invited_users]

        already_invited = []
        for username in usernames:
            if username in invited_usernames:
                already_invited.append(username)

        if already_invited:
            raise serializers.ValidationError(
                _('These users are already invited: %s.') % ', '.join(already_invited)
            )

    def _validate_invite_creator(self, usernames):
        creator_username = ''
        for username in usernames:
            if username == self.event.creator.username:
                creator_username = username

        if creator_username:
            raise serializers.ValidationError(
                _('This user is already the creator of the event: %s.') % creator_username
            )


class CancelInviteMembersSerializer(_EventMembersSerializer):
    member_usernames = ListField(child=serializers.CharField(), allow_empty=False, max_length=100)

    def validate_member_usernames(self, usernames):
        invitations = EventInvitation.objects.filter(user__username__in=usernames)\
                                             .select_related('user')

        self._validate_not_invited(usernames, invitations)
        self._validate_invitation_accepted(usernames, invitations)
        return usernames

    def _validate_not_invited(self, usernames, invitations):
        invited_usernames = [invitation.user.username for invitation in invitations]

        not_invited = []
        for username in usernames:
            if username not in invited_usernames:
                not_invited.append(username)

        if not_invited:
            raise serializers.ValidationError(
                _('These users are not invited: %s.') % ', '.join(not_invited)
            )

    def _validate_invitation_accepted(self, usernames, invitations):
        invitations_accepted = []
        for invitation in invitations:
            if invitation.is_accepted() and invitation.user.username in usernames:
                invitations_accepted.append(invitation.user.username)

        if invitations_accepted:
            raise serializers.ValidationError(
                _('These users already accepted their invitations: %s.') % ', '.join(invitations_accepted)
            )


class RemoveMembersSerializer(_EventMembersSerializer):
    member_pks = ListField(child=PkField(), allow_empty=False, max_length=100)

    def validate_member_pks(self, pks):
        if any(
            pk == self.event.creator.pk
            for pk in pks
        ):
            raise serializers.ValidationError(_('Cannot remove creator of event.'))
        return pks
