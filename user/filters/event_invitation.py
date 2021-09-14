from django_filters import rest_framework as filters

from split_the_bill.models import EventInvitation


class UserEventInvitationFilter(filters.FilterSet):
    class Meta:
        model = EventInvitation
        fields = {
            'event': ['exact'],
            'event__name': ['icontains'],
            'event__creator__nickname': ['icontains'],
            'event__creator__email': ['icontains'],
            'status': ['in'],
            'create_time': ['gte', 'lte'],
            'update_time': ['gte', 'lte'],
        }

    @property
    def qs(self):
        parent = super().qs
        user = self.request.user
        events = user.events_invited_to.all()
        qs = parent.filter(user=user, event__in=events)\
                   .select_related('user', 'event')
        return qs
