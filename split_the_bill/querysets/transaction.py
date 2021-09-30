from django.db import models
from django.db.models import Sum, Value as V
from django.db.models.functions import Coalesce


class TransactionQuerySet(models.QuerySet):
    def transactions_to_fund(self):
        return self.filter(transaction_type=self.model.Types.USER_TO_FUND)

    def expenses(self):
        return self.filter(transaction_type__in=[
            self.model.Types.USER_EXPENSE,
            self.model.Types.FUND_EXPENSE,
        ])

    def total_fund(self):
        return self.transactions_to_fund()\
                   .aggregate(total_fund=Coalesce(Sum('amount'), V(0)))

    def total_expense(self):
        return self.expenses()\
                   .aggregate(total_expense=Coalesce(Sum('amount'), V(0)))
