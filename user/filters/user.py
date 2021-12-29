import django_filters
from django.contrib.auth import get_user_model
from django.db.models.query_utils import Q
from django_filters import rest_framework as filters

User = get_user_model()


class UserFilter(filters.FilterSet):
    class Meta:
        model = User
        fields = {
            'nickname': ['icontains'],
            'email': ['icontains'],
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
        pks = list(set(pks))  # Make unique
        return parent.filter(pk__in=pks)


class UserSearchFilter(filters.FilterSet):
    nickname_or_email__icontains = django_filters.CharFilter(
        required=True,
        method='filter_nickname_or_email',
        label='Nickname or email contains',
    )

    exclude_emails = django_filters.CharFilter(
        required=False,
        method='filter_exclude_emails',
        label='Exclude these emails',
    )

    @property
    def qs(self):
        parent = super().qs
        return parent.exclude(pk=self.request.user.pk)

    def filter_nickname_or_email(self, queryset, name, value):
        # TODO: fuzzy search using MATCH AGAINST?
        condition = Q(nickname__icontains=value) | Q(email__icontains=value)
        return queryset.filter(condition)

    def filter_exclude_emails(self, queryset, name, value):
        emails_to_exclude = map(str.strip, value.split(','))
        return queryset.exclude(email__in=emails_to_exclude)

    class Meta:
        model = User
        fields = ['nickname_or_email__icontains']
