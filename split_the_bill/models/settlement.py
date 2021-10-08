from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

from .event import Event

User = get_user_model()


class Settlement(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='settlements')
    is_paid = models.BooleanField(default=False)
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='settlements_to_pay')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='settlements_to_receive')
    amount = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        ordering = ['event', 'amount']

    @classmethod
    def create_from_cashflows(cls, event, cashflows):
        settlements = []

        for cashflow in cashflows:
            settlement = cls(
                event=event,
                from_user=cashflow.from_user,
                to_user=cashflow.to_user,
                amount=cashflow.amount,
            )
            settlements.append(settlement)

        cls.objects.bulk_create(settlements)
