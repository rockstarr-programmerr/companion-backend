from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsGroupOwnerOrReadonly(BasePermission):
    def has_object_permission(self, request, view, group):
        if request.method in SAFE_METHODS:
            return True
        else:
            is_authenticated = bool(request.user and request.user.is_authenticated)
            is_group_owner = request.user == group.owner
            return is_authenticated and is_group_owner
