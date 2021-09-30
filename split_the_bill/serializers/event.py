from django.utils.translation import gettext as _
from rest_framework import serializers
from rest_framework.fields import ListField
from rest_framework.reverse import reverse

from split_the_bill.models import Event, EventInvitation
from companion.utils.url import update_url_params
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
            'url', 'pk', 'name', 'qr_code',
            'creator', 'members', 'create_time',
            'transactions_url', 'invitations_url', 'extra_action_urls',
        ]
        extra_kwargs = {
            'qr_code': {'read_only': True},
        }

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
            'reset_qr': reverse('event-reset-qr', **kwargs),
            'chart_info': reverse('event-chart-info', **kwargs),
            'settle_expenses': reverse('event-settle-expenses', **kwargs),
        }

    def create(self, validated_data):
        event = super().create(validated_data)
        event.create_qr_code(self.context['request'])
        return event


class _EventMembersSerializer(serializers.Serializer):
    def __init__(self, *args, **kwargs):
        event = None
        if 'event' in kwargs:
            event = kwargs.pop('event')

        super().__init__(*args, **kwargs)

        assert not hasattr(self, 'event'), 'Serializer already has attribute `event`.'
        self.event = event


class InviteMembersSerializer(_EventMembersSerializer):
    member_emails = ListField(child=serializers.EmailField(), allow_empty=False, max_length=100)

    def validate_member_emails(self, emails):
        self._validate_alread_invited(emails)
        self._validate_invite_creator(emails)
        return emails

    def _validate_alread_invited(self, emails):
        invited_users = self.event.invited_users.all()
        invited_emails = [user.email for user in invited_users]

        already_invited = []
        for email in emails:
            if email in invited_emails:
                already_invited.append(email)

        if already_invited:
            raise serializers.ValidationError(
                _('These users are already invited: %s.') % ', '.join(already_invited)
            )

    def _validate_invite_creator(self, emails):
        creator_email = ''
        for email in emails:
            if email == self.event.creator.email:
                creator_email = email

        if creator_email:
            raise serializers.ValidationError(
                _('This user is already the creator of the event: %s.') % creator_email
            )


class CancelInviteMembersSerializer(_EventMembersSerializer):
    member_emails = ListField(child=serializers.CharField(), allow_empty=False, max_length=100)

    def validate_member_emails(self, emails):
        invitations = EventInvitation.objects.filter(user__email__in=emails)\
                                             .select_related('user')

        self._validate_not_invited(emails, invitations)
        self._validate_invitation_accepted(emails, invitations)
        return emails

    def _validate_not_invited(self, emails, invitations):
        invited_emails = [invitation.user.email for invitation in invitations]

        not_invited = []
        for email in emails:
            if email not in invited_emails:
                not_invited.append(email)

        if not_invited:
            raise serializers.ValidationError(
                _('These users are not invited: %s.') % ', '.join(not_invited)
            )

    def _validate_invitation_accepted(self, emails, invitations):
        invitations_accepted = []
        for invitation in invitations:
            if invitation.is_accepted() and invitation.user.email in emails:
                invitations_accepted.append(invitation.user.email)

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


class JoinWithQRCodeSerializer(serializers.Serializer):
    token = serializers.CharField()


class ResetQRCodeSerializer(serializers.Serializer):
    """This serializer is intentionally left blank."""


class ChartInfoSerializer(serializers.Serializer):
    total_fund = serializers.IntegerField()
    total_expense = serializers.IntegerField()


class SettleExpensesSerializer(serializers.Serializer):
    from_user = UserSerializer()
    to_user = UserSerializer()
    amount = serializers.IntegerField()
