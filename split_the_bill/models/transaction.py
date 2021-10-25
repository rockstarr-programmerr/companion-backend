from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models.enums import TextChoices

from split_the_bill.querysets.transaction import TransactionQuerySet

from ._common import TimeStamp
from .event import Event

User = get_user_model()


class Transaction(TimeStamp):
    class Types(TextChoices):
        USER_TO_USER = 'user_to_user'
        USER_TO_FUND = 'user_to_fund'
        FUND_TO_USER = 'fund_to_user'
        USER_EXPENSE = 'user_expense'
        FUND_EXPENSE = 'fund_expense'

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='transactions')
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='transactions_paid')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='transactions_received')
    transaction_type = models.CharField(max_length=12, choices=Types.choices)
    amount = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    description = models.TextField(blank=True)

    objects = TransactionQuerySet.as_manager()

    class Meta:
        ordering = ['-create_time']

    def __str__(self):
        return (f'From {self.from_user} | To {self.to_user} | '
                f'Type: {self.transaction_type} | Amount: {self.amount}')

    @classmethod
    def get_by_event_pk(cls, event_pk):
        condition = {
            cls._meta.get_field('event').attname: event_pk
        }
        return cls.objects.filter(**condition)
