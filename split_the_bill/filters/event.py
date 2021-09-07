from django_filters import rest_framework as filters

from split_the_bill.models import Event


class EventFilter(filters.FilterSet):
    class Meta:
        model = Event
        fields = {
            'name': ['exact', 'icontains'],
            'creator': ['exact'],
            'creator__username': ['exact', 'icontains'],
            'creator__email': ['exact', 'icontains'],
        }
