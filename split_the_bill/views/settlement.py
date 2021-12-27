from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet

from split_the_bill.filters import SettlementFilter
from split_the_bill.models import Settlement
from split_the_bill.serializers.settlement import SettlementSerializer


class SettlementViewSet(mixins.ListModelMixin,
                        mixins.RetrieveModelMixin,
                        mixins.UpdateModelMixin,
                        GenericViewSet):
    queryset = Settlement.objects.all()
    serializer_class = SettlementSerializer
    filterset_class = SettlementFilter
    ordering = ['is_paid']  # Unpaid settlement is order first
