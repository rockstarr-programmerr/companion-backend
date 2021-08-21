from rest_framework.permissions import IsAuthenticated, SAFE_METHODS


class IsGroupOwnerOrReadonly(IsAuthenticated):
    def has_object_permission(self, request, view, group):
        return (
            request.method in SAFE_METHODS or
            request.user == group.owner
        )
