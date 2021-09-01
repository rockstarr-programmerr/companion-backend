from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Q
from django.db.models.enums import TextChoices

from ._common import TimeStamp
from .event import Event

User = get_user_model()


class Transaction(TimeStamp):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='transactions')
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='transactions_paid')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='transactions_received')
    is_deposit = models.BooleanField()
    is_withdrawal = models.BooleanField()
    is_expense = models.BooleanField()

    class Meta:
        ordering = ['-create_time']

    class Types(TextChoices):
        USER_TO_USER = 'user_to_user'
        USER_TO_FUND = 'user_to_fund'
        FUND_TO_USER = 'fund_to_user'
        USER_EXPENSE = 'user_expense'
        FUND_EXPENSE = 'fund_expense'

    def is_user_to_user(self):
        return bool(self.from_user and self.to_user)

    def is_user_to_fund(self):
        return bool(self.is_deposit and self.from_user)

    def is_fund_to_user(self):
        return bool(self.is_withdrawal and self.to_user)

    def is_user_expense(self):
        return bool(self.is_expense and self.from_user)

    def is_fund_expense(self):
        return bool(self.is_expense and self.is_withdrawal)

    def get_transaction_type(self):
        if self.is_user_to_user():
            return self.Types.USER_TO_USER
        if self.is_user_to_fund():
            return self.Types.USER_TO_FUND
        if self.is_fund_to_user():
            return self.Types.FUND_TO_USER
        if self.is_user_expense():
            return self.Types.USER_EXPENSE
        if self.is_fund_expense():
            return self.Types.FUND_EXPENSE

    @classmethod
    def create_transaction(cls, transaction_type, from_user_pk, to_user_pk, **kwargs):
        is_deposit = False
        is_withdrawal = False
        is_expense = False

        if transaction_type == cls.Types.USER_TO_FUND:
            is_deposit = True
        elif transaction_type == cls.Types.FUND_TO_USER:
            is_withdrawal = True
        elif transaction_type == cls.Types.USER_EXPENSE:
            is_expense = True
        elif transaction_type == cls.Types.FUND_EXPENSE:
            is_expense = True
            is_withdrawal = True

        attrs = {
            cls._meta.get_field('from_user').attname: from_user_pk,
            cls._meta.get_field('to_user').attname: to_user_pk,
            'is_deposit': is_deposit,
            'is_withdrawal': is_withdrawal,
            'is_expense': is_expense,
            **kwargs
        }

        transaction = cls.objects.create(**attrs)
        return transaction

    @classmethod
    def filter_transactions(cls, event, start_time=None, end_time=None):
        conditions = Q(event=event)
        if start_time:
            conditions &= Q(create_time__gte=start_time)
        if end_time:
            conditions &= Q(create_time__lte=end_time)

        transactions = cls.objects.filter(conditions)
        return transactions
