from django.utils.translation import gettext as _
from rest_framework import serializers

from split_the_bill.models import Transaction

from ._common import PkField
from .user import UserSerializer


class TransactionSerializer(serializers.ModelSerializer):
    transaction_type = serializers.SerializerMethodField()
    from_user = UserSerializer(required=False)
    to_user = UserSerializer(required=False)

    class Meta:
        model = Transaction
        fields = ['pk', 'transaction_type', 'from_user', 'to_user']

    def get_transaction_type(self, transaction):
        return transaction.get_transaction_type()


class AddTransactionSerializer(serializers.Serializer):
    transaction_type = serializers.ChoiceField(Transaction.Types.choices)
    from_user = PkField(required=False, allow_null=True)
    to_user = PkField(required=False, allow_null=True)

    def validate(self, attrs):
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

        return attrs

    def create(self, validated_data, **kwargs):
        transaction_type = validated_data['transaction_type']
        from_user = validated_data.get('from_user')
        to_user = validated_data.get('to_user')

        transaction = Transaction.create_transaction(transaction_type, from_user, to_user, **kwargs)
        return transaction


class RemoveTransactionSerializer(serializers.Serializer):
    transaction_pk = PkField()
