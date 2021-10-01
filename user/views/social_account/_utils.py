import logging

from allauth.socialaccount.helpers import complete_social_login
from allauth.socialaccount.providers.base import ProviderException
from allauth.socialaccount.providers.oauth2.client import OAuth2Error
from allauth.socialaccount.providers.oauth2.views import OAuth2CallbackView
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext as _
from django.views.decorators.csrf import csrf_exempt
from requests import RequestException
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from user.serializers.social_account import CallbackViewSerializer

logger = logging.getLogger(__name__)


def complete_jwt_login(login):
    user = login.account.user
    token = RefreshToken.for_user(user)
    return {
        'refresh': str(token),
        'access': str(token.access_token),
    }


class MobileAppCallbackView(GenericAPIView, OAuth2CallbackView):
    serializer_class = CallbackViewSerializer
    permission_classes = [AllowAny]

    @classmethod
    def adapter_view(cls, *args, **kwargs):
        view = super().adapter_view(*args, **kwargs)
        return csrf_exempt(view)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        app = self.adapter.get_provider().get_app(self.request)

        try:
            token = self.adapter.parse_token(validated_data)
            token.app = app
            login = self.adapter.complete_login(
                request, app, token, response=validated_data
            )
            login.token = token

            complete_social_login(request, login)
            data = complete_jwt_login(login)
            serializer = self.get_serializer(instance=data)
            return Response(serializer.data)

        except (
            PermissionDenied,
            OAuth2Error,
            RequestException,
            ProviderException,
        ) as e:
            logger.error('Unknown exception when authen user with social account.')
            logger.exception(e)
            return Response(
                data={
                    'detail': _('Failed to authenticate user using social account.')
                },
                status=status.HTTP_401_UNAUTHORIZED
            )
