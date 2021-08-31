from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from split_the_bill.models import Event
from split_the_bill.models.transaction import Transaction
from split_the_bill.permissions import IsEventCreatorOrReadonly, IsEventMembers
from split_the_bill.serializers.event import (AddMembersSerializer,
                                              EventSerializer,
                                              RemoveMembersSerializer)
from split_the_bill.serializers.transaction import (
    AddTransactionSerializer, RemoveTransactionSerializer,
    TransactionSerializer)


class EventViewSet(ModelViewSet):
    serializer_class = EventSerializer
    permission_classes = [IsEventCreatorOrReadonly]

    def get_queryset(self):
        return self.request.user.events_participated.all()

    def perform_create(self, serializer):
        creator = self.request.user
        serializer.save(
            creator=creator,
            members=[creator]  # Auto add `creator` as first member
        )

    @action(
        methods=['POST'], detail=True, url_path='add-members',
        serializer_class=AddMembersSerializer
    )
    def add_members(self, request, pk):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        event = get_object_or_404(Event, pk=pk)
        self.check_object_permissions(request, event)

        member_pks = serializer.validated_data['member_pks']
        event.members.add(*member_pks)

        return Response()

    @action(
        methods=['POST'], detail=True, url_path='remove-members',
        serializer_class=RemoveMembersSerializer
    )
    def remove_members(self, request, pk):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        event = get_object_or_404(Event, pk=pk)
        self.check_object_permissions(request, event)

        member_pks = serializer.validated_data['member_pks']
        event.members.remove(*member_pks)

        return Response()

    @action(
        methods=['POST'], detail=True, url_path='add-transaction',
        serializer_class=AddTransactionSerializer,
        permission_classes=[IsEventMembers]
    )
    def add_transaction(self, request, pk):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        event = get_object_or_404(Event, pk=pk)
        self.check_object_permissions(request, event)

        transaction = serializer.create(serializer.validated_data, event=event)
        serializer = TransactionSerializer(instance=transaction)

        return Response(serializer.data)

    @action(
        methods=['POST'], detail=True, url_path='remove-transaction',
        serializer_class=RemoveTransactionSerializer,
    )
    def remove_transaction(self, request, pk):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        event = get_object_or_404(Event, pk=pk)
        self.check_object_permissions(request, event)

        transaction_pk = serializer.validated_data['transaction_pk']
        transaction = get_object_or_404(Transaction, pk=transaction_pk)
        transaction.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
