from django.conf import settings
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView

from . import root_endpoints


class RootAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        if request.user.is_authenticated:
            data = {
                'my_info': reverse('user-my-info', request=request),
                'my_event_invitations': reverse('user-my-event-invitation-list', request=request),
                'user': request.build_absolute_uri(root_endpoints.USER),
                'split_the_bill': request.build_absolute_uri(root_endpoints.SPLIT_THE_BILL),
            }
        else:
            data = {
                'register': reverse('user-register', request=request),
            }
            if settings.DEBUG:
                data['browsable_api_login'] = reverse('rest_framework:login', request=request)
        return Response(data)
