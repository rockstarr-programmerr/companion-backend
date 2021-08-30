from rest_framework.generics import get_object_or_404
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response

from django.utils.decorators import method_decorator
from django.db import transaction

from split_the_bill.serializers.event import AddMembersSerializer, RemoveMembersSerializer, EventSerializer
from split_the_bill.permissions import IsEventCreatorOrReadonly
from split_the_bill.models import Event


@method_decorator(transaction.atomic, 'post')
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

    @action(methods=['POST'], detail=True, url_path='add-members', url_name='add-members', serializer_class=AddMembersSerializer)
    def add_members(self, request, pk):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        member_pks = serializer.validated_data['member_pks']
        event = get_object_or_404(Event, pk=pk)
        event.members.add(*member_pks)

        return Response()

    @action(methods=['POST'], detail=True, url_path='remove-members', serializer_class=RemoveMembersSerializer)
    def remove_members(self, request, pk):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        member_pks = serializer.validated_data['member_pks']
        event = get_object_or_404(Event, pk=pk)
        event.members.remove(*member_pks)

        return Response()
