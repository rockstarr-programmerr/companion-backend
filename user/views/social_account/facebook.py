import logging
import uuid

from allauth.socialaccount.models import SocialApp
from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter
from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import reverse
from facepy import SignedRequest
from rest_framework.response import Response
from rest_framework.views import APIView

from ._utils import MobileAppCallbackView
from ...models import FacebookDataDeletionRequest

User = get_user_model()

logger = logging.getLogger(__name__)


class MobileAppFacebookAdapter(FacebookOAuth2Adapter):
    pass


callback_view = MobileAppCallbackView.adapter_view(MobileAppFacebookAdapter)


class FacebookDataDeletionCallback(APIView):
    def post(self, request):
        signed_request = request.data['signed_request']
        signed_data = self.parse_signed_request(signed_request)

        confirmation_code = uuid.uuid4().hex

        deletion_request = FacebookDataDeletionRequest.objects.create(
            confirmation_code=confirmation_code,
            issued_at=signed_data['issued_at'],
            expires=signed_data['expires'],
            user_id=signed_data['user_id'],
        )

        try:
            user = User.objects.filter(pk=signed_data['user_id']).first()
            user.delete()
            deletion_request.status = FacebookDataDeletionRequest.Statuses.SUCCESS
            deletion_request.save()
        except Exception as e:
            logger.exception(e)
            deletion_request.status = FacebookDataDeletionRequest.Statuses.FAIL
            deletion_request.save()

        status_url = f'{settings.WEBSITE_URL}/facebook-data-deletion-status?code={confirmation_code}'

        return Response({
            'url': status_url,
            'confirmation_code': confirmation_code,
        })

    def parse_signed_request(self, signed_request):
        secret = self.get_facebook_app_secret()
        signed_data = SignedRequest.parse(signed_request, secret)
        return signed_data

    def get_facebook_app_secret(self):
        if settings.SOCIALACCOUNT_APP_USE_ENV:
            return settings.SOCIALACCOUNT_PROVIDERS['facebook']['APP']['secret']
        else:
            fb_app = SocialApp.objects.get(provider='facebook')
            return fb_app.secret
