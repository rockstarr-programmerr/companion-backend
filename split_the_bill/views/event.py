from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from companion.utils.api import extra_action_urls
from split_the_bill.business.event import EventBusiness, SplitTheBillBusiness
from split_the_bill.filters import EventFilter
from split_the_bill.models import Event, Settlement
from split_the_bill.permissions import IsEventCreatorOrReadonly
from split_the_bill.serializers.event import (CancelInviteMembersSerializer,
                                              ChartInfoSerializer,
                                              EventSerializer,
                                              InviteMembersSerializer,
                                              JoinWithQRCodeSerializer,
                                              PreviewSettlementSerializer,
                                              RemoveMembersSerializer,
                                              ResetQRCodeSerializer,
                                              SettleExpenseSerializer)


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

        member_emails = serializer.validated_data['member_emails']
        event.invite_members_by_emails(member_emails)

        return Response()

    @action(
        methods=['POST'], detail=True, url_path='cancel-invite-members',
        serializer_class=CancelInviteMembersSerializer
    )
    def cancel_invite_members(self, request, pk):
        event = self.get_object()

        serializer = self.get_serializer(data=request.data, event=event)
        serializer.is_valid(raise_exception=True)

        member_emails = serializer.validated_data['member_emails']
        event.cancel_invite_members_by_emails(member_emails)

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
        business = EventBusiness(event)
        business.remove_members(member_pks)

        return Response()

    @action(
        methods=['POST', 'GET'], detail=False, url_path='join-with-qr',
        serializer_class=JoinWithQRCodeSerializer,
        permission_classes=[IsAuthenticatedOrReadOnly]
    )
    def join_with_qr(self, request):
        """
        Join event by scanning a QR code.
        """
        if request.method == 'GET':
            return Response()  # TODO
        else:
            if request.accepted_renderer.format == 'api':
                # When request comes from browsable API, also accept data
                # from POST body for convenience
                serializer = self.get_serializer(data=request.data)
            else:
                serializer = self.get_serializer(data=request.query_params)
            serializer.is_valid(raise_exception=True)
            token = serializer.validated_data['token']
            Event.join_with_qr_code(request.user, token)
            return Response()

    @action(
        methods=['POST'], detail=True, url_path='reset-qr',
        serializer_class=ResetQRCodeSerializer,
    )
    def reset_qr(self, request, pk):
        """
        Get a new QR code for the event.
        Old QR code is immediately invalidated.
        """
        event = self.get_object()
        event.create_qr_code(request, reset_token=True)
        return Response()

    @action(
        methods=['GET'], detail=True, url_path='chart-info',
        serializer_class=ChartInfoSerializer,
    )
    def chart_info(self, request, pk):
        event = self.get_object()
        business = EventBusiness(event)
        total_fund = business.get_total_fund()
        total_expense = business.get_total_expense()
        serializer = self.get_serializer(instance={
            'total_fund': total_fund,
            'total_expense': total_expense,
        })
        return Response(serializer.data)

    @action(
        methods=['GET'], detail=True, url_path='preview-settlements',
        serializer_class=PreviewSettlementSerializer,
    )
    def preview_settlements(self, request, pk):
        """
        Settle expenses for members.

        Query params "?tolerance=<a number greater than or equal to 0>" is supported.
        This amount is the small changes that we can ignore for the sake of simpler transactions.

        Example:
        If the original transaction is "A pay B 12500", and tolerance=1000, then it becomes "A pay B 12000" (500 is ignored).

        Default value if not provided is 1000 (VNĐ).
        """
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        tolerance = serializer.validated_data['tolerance']

        event = self.get_object()
        business = SplitTheBillBusiness(event)
        cash_flows = business.settle(tolerance=tolerance)

        page = self.paginate_queryset(cash_flows)
        serializer = self.get_serializer(instance=page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(
        methods=['POST'], detail=True, url_path='settle',
        serializer_class=SettleExpenseSerializer,
    )
    def settle(self, request, pk):
        """
        Params "tolerance": the small changes that we can ignore for the sake of simpler transactions.

        Example:
        If the original transaction is "A pay B 12500", and tolerance=1000, then it becomes "A pay B 12000" (500 is ignored).

        Default value if not provided is 1000 (VNĐ).
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tolerance = serializer.validated_data['tolerance']

        event = self.get_object()
        event.settle()
        business = SplitTheBillBusiness(event)
        cash_flows = business.settle(tolerance=tolerance)
        Settlement.create_from_cashflows(event, cash_flows)

        return Response()
