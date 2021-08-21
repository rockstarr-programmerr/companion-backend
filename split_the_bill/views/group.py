from rest_framework.viewsets import ModelViewSet

from split_the_bill.serializers.group import GroupSerializer
from split_the_bill.permissions import IsGroupOwnerOrReadonly


class GroupViewSet(ModelViewSet):
    serializer_class = GroupSerializer
    permission_classes = [IsGroupOwnerOrReadonly]

    def get_queryset(self):
        return self.request.user.groups_joined.all()

    def perform_create(self, serializer):
        owner = self.request.user
        serializer.save(
            owner=owner,
            members=[owner]  # Auto add `owner` as first member
        )
