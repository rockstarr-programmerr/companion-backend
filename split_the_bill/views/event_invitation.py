from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet

from companion.utils.api import extra_action_urls
from split_the_bill.filters import EventInvitationFilter
from split_the_bill.models import EventInvitation
from split_the_bill.serializers.event_invitation import \
    EventInvitationRequestSerializer


@extra_action_urls
class EventInvitationViewSet(mixins.ListModelMixin,
                             mixins.RetrieveModelMixin,
                             mixins.CreateModelMixin,
                             mixins.DestroyModelMixin,
                             GenericViewSet):
    queryset = EventInvitation.objects.all()
    serializer_class = EventInvitationRequestSerializer
    filterset_class = EventInvitationFilter
    ordering_fields = ['username', 'create_time', 'update_time']
    ordering = ['create_time']
