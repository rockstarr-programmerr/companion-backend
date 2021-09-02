from split_the_bill.filters.transaction import TransactionFilter
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
    AddTransactionSerializer, GetTransactionsSerializer, RemoveTransactionSerializer,
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
        permission_classes=[IsEventMembers]
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

    @action(
        methods=['GET'], detail=True, url_path='get-transactions',
        serializer_class=GetTransactionsSerializer,
        permission_classes=[IsEventMembers]
    )
    def get_transactions(self, request, pk):
        """
        Filter transactions within a time range. Support timezone.
        `start_time` and `end_time` parameters use ISO-8601 datetime format
        """
        # serializer = self.get_serializer(data=request.query_params)
        # serializer.is_valid(raise_exception=True)

        event = get_object_or_404(Event, pk=pk)
        self.check_object_permissions(request, event)

        f = TransactionFilter(request.query_params, queryset=Transaction.filter_transactions(event))

        # start_time = serializer.validated_data.get('start_time')
        # end_time = serializer.validated_data.get('end_time')
        # transactions = Transaction.filter_transactions(event, start_time=start_time, end_time=end_time)

        page = self.paginate_queryset(f.qs)
        serializer = TransactionSerializer(instance=page, many=True)
        return self.get_paginated_response(serializer.data)
