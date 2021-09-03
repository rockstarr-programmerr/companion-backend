from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from companion.utils.serializers import ExtraDetailActionUrlsMixin
from split_the_bill.models import Transaction

from ._common import CustomChoiceField


class TransactionSerializer(ExtraDetailActionUrlsMixin, serializers.HyperlinkedModelSerializer):
    transaction_type = CustomChoiceField(choices=Transaction.Types.choices)
    extra_action_urls = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Transaction
        fields = [
            'url', 'pk', 'event',
            'transaction_type', 'from_user', 'to_user', 'amount',
            'create_time', 'update_time', 'extra_action_urls',
        ]

    def validate_event(self, event):
        logged_in_user = self.context['request'].user
        if event not in logged_in_user.events_participated.all():
            raise PermissionDenied(_("You don't have permission for this event."))
        return event

    def validate(self, attrs):
        self._validate_from_to_user_are_different(attrs)
        self._validate_user_is_event_member(attrs)
        self._validate_transaction_logic(attrs)
        return attrs

    def _validate_from_to_user_are_different(self, attrs):
        from_user = attrs.get('from_user')
        to_user = attrs.get('to_user')
        if (
            from_user and to_user and
            from_user == to_user
        ):
            raise serializers.ValidationError(
                _("`from_user` and `to_user` must be different.")
            )

    def _validate_user_is_event_member(self, attrs):
        event = attrs['event']
        from_user = attrs.get('from_user')
        to_user = attrs.get('to_user')

        members = event.members.all()
        if (
            (from_user and from_user not in members) or
            (to_user and to_user not in members)
        ):
            raise serializers.ValidationError(
                _("`from_user` and `to_user` must be one of event's members.")
            )

    def _validate_transaction_logic(self, attrs):
        transaction_type = attrs['transaction_type']
        from_user = attrs.get('from_user')
        to_user = attrs.get('to_user')

        if (
            transaction_type == Transaction.Types.USER_TO_USER and
            not bool(from_user and to_user)
        ):
            raise serializers.ValidationError(
                _('If `transaction_type` is "user_to_user" then both `from_user` and `to_user` are required.')
            )

        elif (
            transaction_type == Transaction.Types.USER_TO_FUND and
            bool(not from_user or to_user)
        ):
            raise serializers.ValidationError(
                _('If `transaction_type` is "user_to_fund" then `from_user` is required and `to_user` must be null.')
            )

        elif (
            transaction_type == Transaction.Types.FUND_TO_USER and
            bool(not to_user or from_user)
        ):
            raise serializers.ValidationError(
                _('If `transaction_type` is "fund_to_user" then `to_user` is required and `from_user` must be null.')
            )

        elif (
            transaction_type == Transaction.Types.USER_EXPENSE and
            bool(not from_user or to_user)
        ):
            raise serializers.ValidationError(
                _('If `transaction_type` is "user_expense" then `from_user` is required and `to_user` must be null.')
            )

        elif (
            transaction_type == Transaction.Types.FUND_EXPENSE and
            bool(from_user or to_user)
        ):
            raise serializers.ValidationError(
                _('If `transaction_type` is "fund_expense" then both `from_user` and `to_user` must be null.')
            )
