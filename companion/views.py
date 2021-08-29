from rest_framework.views import APIView
from rest_framework.response import Response

from . import root_endpoints


class RootAPIView(APIView):
    def get(self, request):
        data = {
            'user': request.build_absolute_uri(root_endpoints.USER),
            'split_the_bill': request.build_absolute_uri(root_endpoints.SPLIT_THE_BILL),
        }
        return Response(data)
