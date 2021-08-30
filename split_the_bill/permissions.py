from django.utils.translation import gettext_lazy as _
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated


class _IsCreatorOrReadonly(IsAuthenticated):
    creator_field_name = ''

    def has_object_permission(self, request, view, obj):
        return (
            request.method in SAFE_METHODS or
            request.user == getattr(obj, self.creator_field_name)
        )


class IsGroupOwnerOrReadonly(_IsCreatorOrReadonly):
    creator_field_name = 'owner'
    message = _('Only group owner has permission for this.')


class IsEventCreatorOrReadonly(_IsCreatorOrReadonly):
    creator_field_name = 'creator'
    message = _('Only event creator has permission for this.')


class IsEventMembers(IsAuthenticated):
    message = _('Only event members can execute this action.')

    def has_object_permission(self, request, view, event):
        return request.user in event.members.all()
