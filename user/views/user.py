from django.contrib.auth import get_user_model, login
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views.decorators.debug import sensitive_post_parameters
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.reverse import reverse_lazy
from rest_framework.viewsets import GenericViewSet

from companion.utils.api import extra_action_urls
from user.business.reset_password import (ResetPasswordBusiness,
                                          ResetPasswordTokenInvalid)
from user.filters import UserFilter, UserSearchFilter
from user.pagination import UserSearchPagination
from user.permissions import IsSelfOrReadOnly
from user.serializers.user import (ChangePasswordSerializer,
                                   EmailResetPasswordLinkSerializer,
                                   RegisterSerializer, ResetPasswordSerializer,
                                   UserSearchSerializer, UserSerializer)

User = get_user_model()


@extra_action_urls({
    'my_info': reverse_lazy('user-my-info'),  # Backward-compat
})
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
    "users/login/": Login with credential (email, password), response with "access" and "refresh" token.
    "users/token-refresh/": Refresh token, response with another "access" and "refresh" token.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filterset_class = UserFilter
    permission_classes = [IsSelfOrReadOnly]
    ordering_fields = ['nickname', 'email']
    ordering = ['nickname']

    @action(
        detail=False, methods=['POST'], url_path='register',
        serializer_class=RegisterSerializer,
        permission_classes=[AllowAny]
    )
    def register(self, request):
        """
        Register user.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        user = User.objects.create_user(email=email, password=password)

        serializer = self.get_serializer(instance=user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        detail=False, methods=['GET'], url_path='search',
        serializer_class=UserSearchSerializer,
        filterset_class=UserSearchFilter,
        pagination_class=UserSearchPagination,
        ordering_fields=['nickname', 'email']
    )
    def search(self, request):
        """
        Search for user by nickname or email.
        """
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(instance=page, many=True)
        return self.get_paginated_response(serializer.data)

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
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        return Response()

    @action(
        detail=False, methods=['POST'],
        url_path='email-reset-password-link',
        serializer_class=EmailResetPasswordLinkSerializer,
        permission_classes=[AllowAny],
    )
    def email_reset_password_link(self, request):
        """
        Send reset password link email.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        deeplink = serializer.validated_data['deeplink']
        email = serializer.validated_data['email']

        user = ResetPasswordBusiness.get_user_by_email(email)
        if user:
            business = ResetPasswordBusiness(user)
            business.send_email(deeplink)

        return Response(status=status.HTTP_202_ACCEPTED)

    @action(
        detail=False, methods=['POST'],
        url_path='reset-password',
        serializer_class=ResetPasswordSerializer,
        permission_classes=[AllowAny],
    )
    def reset_password(self, request):
        """
        Reset user's password.
        For `deeplink`, you must config the `ALLOWED_DEEPLINKS` variable in `companion/settings.py`
        Return 403 if `token` is not valid.
        Return 404 if `uid` is not valid.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        uid = serializer.validated_data['uid']
        token = serializer.validated_data['token']
        password = serializer.validated_data['password']

        user = ResetPasswordBusiness.get_user_by_uid(uid)
        if user:
            business = ResetPasswordBusiness(user)
            try:
                business.reset_password(password, token)
            except ResetPasswordTokenInvalid:
                raise PermissionDenied(_('Reset password token invalid.'))
        else:
            raise NotFound(_('Cannot find user with the given `uid`.'))

        return Response()
