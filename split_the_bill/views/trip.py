from rest_framework.generics import get_object_or_404
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response

from split_the_bill.serializers.trip import AddMembersSerializer, RemoveMembersSerializer, TripSerializer
from split_the_bill.permissions import IsTripCreatorOrReadonly
from split_the_bill.models import Trip


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

    @action(methods=['POST'], detail=True, url_path='add-members', url_name='add-members', serializer_class=AddMembersSerializer)
    def add_members(self, request, pk):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        member_pks = serializer.validated_data['member_pks']
        trip = get_object_or_404(Trip, pk=pk)
        trip.members.add(*member_pks)

        return Response()

    @action(methods=['POST'], detail=True, url_path='remove-members', serializer_class=RemoveMembersSerializer)
    def remove_members(self, request, pk):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        member_pks = serializer.validated_data['member_pks']
        trip = get_object_or_404(Trip, pk=pk)
        trip.members.remove(*member_pks)

        return Response()
