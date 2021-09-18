from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from companion.utils.api import extra_action_urls
from split_the_bill.models import EventInvitation
from user.business.event_invitation import EventInvitationBusiness
from user.filters import UserEventInvitationFilter
from user.serializers.event_invitation import UserEventInvitationSerializer


@extra_action_urls
class UserEventInvitationViewSet(ReadOnlyModelViewSet):
    queryset = EventInvitation.objects.all()
    filterset_class = UserEventInvitationFilter
    serializer_class = UserEventInvitationSerializer
    ordering_fields = ['create_time', 'update_time', 'event__name', 'status']
    ordering = ['-create_time']

    @action(
        methods=['POST'], detail=True,
        url_path='accept',
    )
    def accept(self, request, pk):
        invitation = self.get_object()
        business = EventInvitationBusiness(invitation)
        business.accept()
        return Response()

    @action(
        methods=['POST'], detail=True,
        url_path='decline',
    )
    def decline(self, request, pk):
        invitation = self.get_object()
        business = EventInvitationBusiness(invitation)
        business.decline()
        return Response()
