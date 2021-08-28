from rest_framework.viewsets import ModelViewSet

from split_the_bill.serializers.trip import TripSerializer
from split_the_bill.permissions import IsTripCreatorOrReadonly


class TripViewSet(ModelViewSet):
    serializer_class = TripSerializer
    permission_classes = [IsTripCreatorOrReadonly]

    def get_queryset(self):
        return self.request.user.trips_participated.all()

    def perform_create(self, serializer):
        creator = self.request.user
        serializer.save(
            creator=creator,
            members=[creator]  # Auto add `creator` as first member
        )
