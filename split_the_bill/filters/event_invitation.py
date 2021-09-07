from django_filters import rest_framework as filters

from split_the_bill.models import EventInvitation


class EventInvitationFilter(filters.FilterSet):
    class Meta:
        model = EventInvitation
        fields = {
            'event': ['exact'],
            'user': ['exact'],
            'user__username': ['icontains'],
            'status': ['in'],
            'create_time': ['gte', 'lte'],
            'update_time': ['gte', 'lte'],
        }

    @property
    def qs(self):
        parent = super().qs
        events = self.request.user.events_participated.all()
        qs = parent.filter(event__in=events)\
                   .select_related('user', 'event')
        return qs
