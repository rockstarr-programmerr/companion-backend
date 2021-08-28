from rest_framework.permissions import IsAuthenticated, SAFE_METHODS


class _IsCreatorOrReadonly(IsAuthenticated):
    creator_field_name = ''

    def has_object_permission(self, request, view, obj):
        return (
            request.method in SAFE_METHODS or
            request.user == getattr(obj, self.creator_field_name)
        )


class IsGroupOwnerOrReadonly(_IsCreatorOrReadonly):
    creator_field_name = 'owner'


class IsTripCreatorOrReadonly(_IsCreatorOrReadonly):
    creator_field_name = 'creator'
