from rest_framework.viewsets import ModelViewSet

from companion.utils.api import add_extra_action_urls
from split_the_bill.permissions import IsGroupOwnerOrReadonly
from split_the_bill.serializers.group import GroupSerializer


@add_extra_action_urls
class GroupViewSet(ModelViewSet):
    serializer_class = GroupSerializer
    permission_classes = [IsGroupOwnerOrReadonly]
    ordering_fields = ['name', 'create_time', 'update_time']
    ordering = ['-create_time']

    def get_queryset(self):
        return self.request.user.groups_joined.all()

    def perform_create(self, serializer):
        owner = self.request.user
        serializer.save(
            owner=owner,
            members=[owner]  # Auto add `owner` as first member
        )
