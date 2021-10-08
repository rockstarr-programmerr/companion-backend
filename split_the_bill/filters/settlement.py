from django_filters import rest_framework as filters

from split_the_bill.models import Settlement


class SettlementFilter(filters.FilterSet):
    class Meta:
        model = Settlement
        fields = {
            'event': ['exact'],
            'from_user': ['exact'],
            'to_user': ['exact'],
            'amount': ['gte', 'lte'],
        }

    @property
    def qs(self):
        parent = super().qs
        events = self.request.user.events_participated.all()
        qs = parent.filter(event__in=events).select_related('from_user', 'to_user')
        return qs
