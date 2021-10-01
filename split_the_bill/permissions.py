from django.utils.translation import gettext_lazy as _
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated


class IsGroupOwnerOrReadonly(IsAuthenticated):
    message = _('Only group owner has permission for this.')

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        else:
            if not hasattr(obj, 'owner'):
                obj = obj.group
            return request.user == obj.owner


class IsEventCreatorOrReadonly(IsAuthenticated):
    message = _('Only event creator has permission for this.')

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        else:
            if not hasattr(obj, 'creator'):
                obj = obj.event
            request.user == obj.creator


class IsEventMembers(IsAuthenticated):
    message = _('Only event members can execute this action.')

    def has_object_permission(self, request, view, obj):
        if not hasattr(obj, 'members'):
            obj = obj.event
        return request.user in obj.members.all()
