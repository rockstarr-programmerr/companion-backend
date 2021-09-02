from rest_framework.viewsets import ModelViewSet

from split_the_bill.serializers.transaction import TransactionSerializer
from split_the_bill.models import Transaction


class TransactionViewSet(ModelViewSet):
    serializer_class = TransactionSerializer

    def get_queryset(self):
        events = self.request.user.events_participated.all()
        qs = Transaction.objects.filter(event__in=events)\
                                .select_related('from_user', 'to_user', 'event')\
                                .prefetch_related('event__members')
        return qs
