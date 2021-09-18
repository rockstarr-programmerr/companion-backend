from django_filters import rest_framework as filters

from split_the_bill.models import Transaction


class TransactionFilter(filters.FilterSet):
    class Meta:
        model = Transaction
        fields = {
            'event': ['exact'],
            'transaction_type': ['exact'],
            'from_user': ['exact'],
            'from_user__nickname': ['icontains'],
            'from_user__email': ['icontains'],
            'to_user': ['exact'],
            'to_user__nickname': ['icontains'],
            'to_user__email': ['icontains'],
            'amount': ['gte', 'lte'],
            'create_time': ['gte', 'lte'],
            'update_time': ['gte', 'lte'],
        }

    @property
    def qs(self):
        parent = super().qs
        events = self.request.user.events_participated.all()
        qs = parent.filter(event__in=events)\
                   .select_related('from_user', 'to_user', 'event')\
                   .prefetch_related('event__members')
        return qs
