from rest_framework.permissions import IsAuthenticated, SAFE_METHODS


class IsSelfOrReadOnly(IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        return (
            request.method in SAFE_METHODS or
            request.user == obj
        )
