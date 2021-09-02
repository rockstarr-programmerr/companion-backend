from django.contrib.auth import get_user_model
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from user.filters import UserFilter, UserSearchFilter
from user.permissions import IsSelfOrReadOnly
from user.serializers.user import RegisterSerializer, UserSerializer, UserSearchSerializer

User = get_user_model()


class UserViewSet(mixins.RetrieveModelMixin,
                  mixins.UpdateModelMixin,
                  mixins.DestroyModelMixin,
                  mixins.ListModelMixin,
                  GenericViewSet):
    """
    Only show users who participated the same events as the logged in user.

    Endpoints for authentication:
    "user/login/": Login with credential (username, password), response with "access" and "refresh" token.
    "user/token-refresh/": Refresh token, response with another "access" and "refresh" token.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filterset_class = UserFilter
    permission_classes = [IsSelfOrReadOnly]

    @action(
        detail=False, methods=['POST'], url_path='register',
        serializer_class=RegisterSerializer,
        permission_classes=[AllowAny]
    )
    def register(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data['username']
        email = serializer.validated_data.get('email')
        password = serializer.validated_data['password']

        user = User.objects.create_user(username, email=email, password=password)

        serializer = self.get_serializer(instance=user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        detail=False, methods=['GET'], url_name='search',
        serializer_class=UserSearchSerializer,
        filterset_class=UserSearchFilter
    )
    def search(self, request):
        """
        When searching by username, only username are returned, not all user's info
        """
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(instance=queryset, many=True)
        return Response(serializer.data)
