from django.db.models import TextChoices
from django.utils.translation import gettext as _
from rest_framework import serializers

from split_the_bill.models import Transaction

from ._common import PkField
from .user import UserSerializer


class _TransactionTypes(TextChoices):
    USER_TO_USER = 'user_to_user'
    USER_TO_FUND = 'user_to_fund'
    FUND_TO_USER = 'fund_to_user'
    USER_EXPENSE = 'user_expense'
    FUND_EXPENSE = 'fund_expense'


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = [
            'pk',
            'from_user',
            'to_user',
            'is_deposit',
            'is_withdrawal',
            'is_expense',
        ]


class AddTransactionSerializer(serializers.Serializer):
    transaction_type = serializers.ChoiceField(_TransactionTypes.choices)
    from_user = UserSerializer(required=False)
    to_user = UserSerializer(required=False)

    def validate(self, attrs):
        transaction_type = attrs['transaction_type']
        from_user = attrs.get('from_user')
        to_user = attrs.get('to_user')

        if (
            transaction_type == _TransactionTypes.USER_TO_USER and
            not bool(from_user and to_user)
        ):
            raise serializers.ValidationError(
                _('If `transaction_type` is "user_to_user" then both `from_user` and `to_user` are required.')
            )

        elif (
            transaction_type == _TransactionTypes.USER_TO_FUND and
            bool(not from_user or to_user)
        ):
            raise serializers.ValidationError(
                _('If `transaction_type` is "user_to_fund" then `from_user` is required and `to_user` must be null.')
            )

        elif (
            transaction_type == _TransactionTypes.FUND_TO_USER and
            bool(not to_user or from_user)
        ):
            raise serializers.ValidationError(
                _('If `transaction_type` is "fund_to_user" then `to_user` is required and `from_user` must be null.')
            )

        elif (
            transaction_type == _TransactionTypes.USER_EXPENSE and
            bool(not from_user or to_user)
        ):
            raise serializers.ValidationError(
                _('If `transaction_type` is "user_expense" then `from_user` is required and `to_user` must be null.')
            )

        elif (
            transaction_type == _TransactionTypes.FUND_EXPENSE and
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
        is_deposit = False
        is_withdrawal = False
        is_expense = False

        if from_user and not to_user:
            if transaction_type == _TransactionTypes.USER_TO_FUND:
                is_deposit = True
            elif transaction_type == _TransactionTypes.USER_EXPENSE:
                is_expense = True
        elif to_user and not from_user:
            is_withdrawal = True
        elif not from_user and not to_user:
            is_expense = True

        transaction = Transaction.objects.create(
            from_user=from_user,
            to_user=to_user,
            is_deposit=is_deposit,
            is_withdrawal=is_withdrawal,
            is_expense=is_expense,
            **kwargs
        )

        return transaction


class RemoveTransactionSerializer(serializers.Serializer):
    transaction_pk = PkField()
