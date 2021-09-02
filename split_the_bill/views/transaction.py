from rest_framework.viewsets import ModelViewSet

from split_the_bill.filters import TransactionFilter
from split_the_bill.models import Transaction
from split_the_bill.serializers.transaction import TransactionSerializer


class TransactionViewSet(ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    filterset_class = TransactionFilter
    ordering_fields = ['amount', 'create_time', 'update_time']
    ordering = ['-create_time']
