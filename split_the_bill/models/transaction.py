from django.db import models
from django.contrib.auth import get_user_model

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
