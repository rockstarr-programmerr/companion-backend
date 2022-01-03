import json
import logging
import uuid
from datetime import datetime

from allauth.socialaccount.models import SocialApp
from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter
from django.conf import settings
from django.contrib.auth import get_user_model
from facepy import SignedRequest
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from ...models import FacebookDataDeletionRequest
from ...serializers.social_account import FbDataDeletionStatusSerializer
from ._utils import MobileAppCallbackView

User = get_user_model()

logger = logging.getLogger(__name__)


class MobileAppFacebookAdapter(FacebookOAuth2Adapter):
    pass


callback_view = MobileAppCallbackView.adapter_view(MobileAppFacebookAdapter)


class DataDeletionCallback(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        signed_request = request.data['signed_request']
        signed_data = self.parse_signed_request(signed_request)

        confirmation_code = uuid.uuid4().hex

        data = {
            'confirmation_code': confirmation_code,
            'issued_at': None,
            'expires': None,
            'user_id': signed_data.get('user_id'),
        }
        issued_at = signed_data.get('issued_at')
        expires = signed_data.get('expires')

        if isinstance(issued_at, int):
            data['issued_at'] = datetime.fromtimestamp(issued_at)
        if isinstance(expires, int):
            data['expires'] = datetime.fromtimestamp(expires)

        deletion_request = FacebookDataDeletionRequest.objects.create(**data)

        try:
            user = User.objects.filter(pk=signed_data['user_id']).first()
            user.delete()
            deletion_request.status = FacebookDataDeletionRequest.Statuses.SUCCESS
            deletion_request.save()
        except Exception as e:
            logger.exception(e)
            logger.error(json.dumps(signed_data))
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


class DataDeletionStatus(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        confirmation_code = request.query_params.get('code') or ''
        data = {
            'confirmation_code': confirmation_code,
            'status': '',
            'issued_at': None,
            'expires': None,
        }

        status = FacebookDataDeletionRequest.objects.filter(confirmation_code=confirmation_code).first()
        if status:
            data['status'] = status.status
            data['issued_at'] = status.issued_at
            data['expires'] = status.expires

        serializer = FbDataDeletionStatusSerializer(instance=data)
        return Response(serializer.data)
