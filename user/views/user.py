from django.contrib.auth import get_user_model, login
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views.decorators.debug import sensitive_post_parameters
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from companion.utils.api import extra_action_urls
from user.filters import UserFilter, UserSearchFilter
from user.pagination import UserSearchPagination
from user.permissions import IsSelfOrReadOnly
from user.serializers.user import (ChangePasswordSerializer,
                                   EmailResetPasswordLinkSerializer,
                                   RegisterSerializer, UserSearchSerializer,
                                   UserSerializer)
from user.business import reset_password

User = get_user_model()


@extra_action_urls
@method_decorator(
    sensitive_post_parameters(
        'password', 'new_password', 'current_password'
    ),
    name='dispatch'
)
class UserViewSet(mixins.RetrieveModelMixin,
                  mixins.UpdateModelMixin,
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
    ordering_fields = ['username', 'email']
    ordering = ['username']

    @action(
        detail=False, methods=['POST'], url_path='register',
        serializer_class=RegisterSerializer,
        permission_classes=[AllowAny]
    )
    def register(self, request):
        """
        Register user.
        `email` is not required, but must be unique if provided.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data['username']
        email = serializer.validated_data.get('email')
        password = serializer.validated_data['password']

        user = User.objects.create_user(username, email=email, password=password)

        serializer = self.get_serializer(instance=user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        detail=False, methods=['GET'], url_path='search',
        serializer_class=UserSearchSerializer,
        filterset_class=UserSearchFilter,
        pagination_class=UserSearchPagination,
        ordering_fields=['username']
    )
    def search(self, request):
        """
        When searching by username, only username are returned, not all user's info
        """
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(instance=page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(
        detail=False, methods=['GET', 'PUT', 'PATCH'],
        url_path='my-info',
    )
    def my_info(self, request):
        """
        Get/update information of current logged-in user
        """
        if request.method == 'GET':
            serializer = self.get_serializer(instance=request.user)
            return Response(serializer.data)
        else:
            partial = request.method == 'PATCH'
            serializer = self.get_serializer(instance=request.user, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response(serializer.data)

    @action(
        detail=False, methods=['POST'],
        url_path='change-password',
        serializer_class=ChangePasswordSerializer,
    )
    def change_password(self, request):
        """
        Change logged-in user's password, return 403 if `current_password` is not correct.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        current_password = serializer.validated_data['current_password']
        new_password = serializer.validated_data['new_password']

        user = self.request.user
        if not user.check_password(current_password):
            raise PermissionDenied(_('Wrong password.'))

        user.set_password(new_password)
        user.save()
        login(request, user)
        return Response()

    @action(
        detail=False, methods=['POST'],
        url_path='email-reset-password-link',
        serializer_class=EmailResetPasswordLinkSerializer,
        permission_classes=[AllowAny],
    )
    def email_reset_password_link(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        deeplink = serializer.validated_data['deeplink']
        email = serializer.validated_data['email']

        user = User.get_user_by_email(email)
        if user:
            reset_password.send_email(user, deeplink)

        return Response()
