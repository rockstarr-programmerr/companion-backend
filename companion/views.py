from django.conf import settings
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView

from . import root_endpoints


class RootAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        if not request.user.is_authenticated:
            data = {
                'browsable_api_login': reverse('rest_framework:login', request=request)
            }
        elif request.user.is_staff:
            data = {
                'split_the_bill': request.build_absolute_uri(root_endpoints.SPLIT_THE_BILL),
                'account': {
                    'my_info': reverse('user-my-info', request=request),
                    'my_event_invitations': reverse('user-my-event-invitation-list', request=request),
                    'user': request.build_absolute_uri(root_endpoints.USER),
                },
                'authen': {
                    'register': reverse('user-register', request=request),
                    'login': reverse('token_obtain_pair', request=request),
                    'refresh_token': reverse('token_refresh', request=request),
                    'social_authen': {
                        'google': reverse('social_account_google_authen', request=request),
                        'facebook': reverse('social_account_facebook_authen', request=request),
                    },
                    'email_reset_password_link': reverse('user-email-reset-password-link', request=request),
                    'reset_password': reverse('user-reset-password', request=request),
                },
                'test_error_logging': reverse('companion-test-error-logging', request=request),
            }
        else:
            data = {}

        return Response(data)


class TestErrorLoggingAPIView(APIView):
    """
    When POST, an unhandled exception will be raised on the server.
    """
    permission_classes = [IsAdminUser]

    def post(self, request):
        raise NameError('Uvuvuwevwev')
