from django.utils.translation import gettext as _
from rest_framework import serializers

from split_the_bill.models import EventInvitation


class EventInvitationBusiness:
    def __init__(self, invitation):
        self.invitation = invitation

    def accept(self):
        self._update_status(EventInvitation.Statuses.ACCEPTED)
        self._add_member()

    def decline(self):
        self._validate_status_before_decline()
        self._update_status(EventInvitation.Statuses.DECLINED)

    def _update_status(self, status):
        self.invitation.status = status
        self.invitation.save()

    def _validate_status_before_decline(self):
        if self.invitation.status != EventInvitation.Statuses.PENDING:
            raise serializers.ValidationError(
                _('This invitation has already been accepted.')
            )

    def _add_member(self):
        invited_user = self.invitation.user
        event = self.invitation.event
        event.members.add(invited_user)
