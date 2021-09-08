from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet
from rest_framework.generics import get_object_or_404
from rest_framework import mixins

from user.serializers.user import MyInfoSerializer

User = get_user_model()


class MyInfoViewSet(mixins.RetrieveModelMixin,
                    mixins.UpdateModelMixin,
                    GenericViewSet):
    """
    Get/update information of current logged-in user.

    To update avatar: send image with Content-Type = multipart/form-data
    To remove avatar: send request with {"avatar": null}
    """
    queryset = User.objects.all()
    serializer_class = MyInfoSerializer
    permission_classes = [IsAuthenticated]
    ordering_fields = []
    ordering = []

    def get_object(self):
        return get_object_or_404(self.get_queryset(), pk=self.request.user.pk)
