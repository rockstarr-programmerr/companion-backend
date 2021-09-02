from django_filters import rest_framework as filters

from split_the_bill.models import Transaction


class TransactionFilter(filters.FilterSet):
    class Meta:
        model = Transaction
        fields = {
            'from_user': ['exact'],
            'from_user__username': ['icontains'],
            'from_user__email': ['icontains'],
            'to_user': ['exact'],
            'to_user__username': ['icontains'],
            'to_user__email': ['icontains'],
            'create_time': ['gte', 'lte'],
            'update_time': ['gte', 'lte'],
        }

    def to_html(self, request, queryset, view):
        return '<h1>Hello internet</h1>'
