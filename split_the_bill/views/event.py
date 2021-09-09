from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from companion.utils.api import extra_action_urls
from split_the_bill.filters import EventFilter
from split_the_bill.permissions import IsEventCreatorOrReadonly
from split_the_bill.serializers.event import (CancelInviteMembersSerializer,
                                              EventSerializer,
                                              InviteMembersSerializer,
                                              RemoveMembersSerializer)


@extra_action_urls
class EventViewSet(ModelViewSet):
    serializer_class = EventSerializer
    filterset_class = EventFilter
    permission_classes = [IsEventCreatorOrReadonly]
    ordering_fields = ['name', 'create_time', 'update_time']
    ordering = ['-create_time']

    def get_queryset(self):
        return self.request.user.events_participated.all()

    def perform_create(self, serializer):
        creator = self.request.user
        serializer.save(
            creator=creator,
            members=[creator]  # Auto add `creator` as first member
        )

    @action(
        methods=['POST'], detail=True, url_path='invite-members',
        serializer_class=InviteMembersSerializer
    )
    def invite_members(self, request, pk):
        event = self.get_object()

        serializer = self.get_serializer(data=request.data, event=event)
        serializer.is_valid(raise_exception=True)

        member_usernames = serializer.validated_data['member_usernames']
        event.invite_members_by_usernames(member_usernames)

        return Response()

    @action(
        methods=['POST'], detail=True, url_path='cancel-invite-members',
        serializer_class=CancelInviteMembersSerializer
    )
    def cancel_invite_members(self, request, pk):
        event = self.get_object()

        serializer = self.get_serializer(data=request.data, event=event)
        serializer.is_valid(raise_exception=True)

        member_usernames = serializer.validated_data['member_usernames']
        event.cancel_invite_members_by_usernames(member_usernames)

        return Response()

    @action(
        methods=['POST'], detail=True, url_path='remove-members',
        serializer_class=RemoveMembersSerializer
    )
    def remove_members(self, request, pk):
        event = self.get_object()

        serializer = self.get_serializer(data=request.data, event=event)
        serializer.is_valid(raise_exception=True)

        member_pks = serializer.validated_data['member_pks']
        event.members.remove(*member_pks)

        return Response()
