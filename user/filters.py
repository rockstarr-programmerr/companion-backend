from django_filters import rest_framework as filters
from django.contrib.auth import get_user_model

User = get_user_model()


class UserFilter(filters.FilterSet):
    class Meta:
        model = User
        fields = {
            'username': ['icontains'],
        }

    @property
    def qs(self):
        parent = super().qs
        events = self.request.user.events_participated.all().prefetch_related('members')
        members = []
        for event in events:
            members.extend(event.members.all())
        member_pks = [member.pk for member in members]
        return parent.filter(pk__in=member_pks)
