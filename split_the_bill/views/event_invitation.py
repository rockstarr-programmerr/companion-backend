from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet

from companion.utils.api import extra_action_urls
from split_the_bill.filters import EventInvitationFilter
from split_the_bill.models import EventInvitation
from split_the_bill.serializers.event_invitation import \
    EventInvitationRequestSerializer
from split_the_bill.permissions import IsEventCreatorOrReadonly


@extra_action_urls
class EventInvitationViewSet(mixins.ListModelMixin,
                             mixins.RetrieveModelMixin,
                             mixins.CreateModelMixin,
                             mixins.DestroyModelMixin,
                             GenericViewSet):
    """
    CRD operations for event invitations (update is not allowed).
    An invitation has 3 statuses: "pending", "accepted", "declined".
    """
    queryset = EventInvitation.objects.all()
    serializer_class = EventInvitationRequestSerializer
    filterset_class = EventInvitationFilter
    permission_classes = [IsEventCreatorOrReadonly]
    ordering_fields = ['username', 'create_time', 'update_time']
    ordering = ['create_time']
