from django.db import models


class TransactionQuerySet(models.QuerySet):
    def transactions_to_fund(self):
        return self.filter(transaction_type=self.model.Types.USER_TO_FUND)

    def expenses(self):
        return self.filter(transaction_type__in=[
            self.model.Types.USER_EXPENSE,
            self.model.Types.FUND_EXPENSE,
        ])
