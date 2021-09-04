import django_filters
from django.contrib.auth import get_user_model
from django.core.validators import MinLengthValidator
from django_filters import rest_framework as filters

User = get_user_model()


class UserFilter(filters.FilterSet):
    class Meta:
        model = User
        fields = {
            'username': ['icontains'],
        }

    @property
    def qs(self):
        """
        Filter only users who participated the same events as the logged in user.
        """
        parent = super().qs
        events = self.request.user.events_participated.all().prefetch_related('members')
        members = []
        for event in events:
            members.extend(event.members.all())
        member_pks = [member.pk for member in members]

        pks = member_pks + [self.request.user.pk]
        return parent.filter(pk__in=pks)


class UserSearchFilter(filters.FilterSet):
    username__icontains = django_filters.CharFilter(
        field_name='username',
        lookup_expr='icontains',
        required=True,
        validators=[MinLengthValidator(3)]
    )

    class Meta:
        model = User
        fields = ['username__icontains']
