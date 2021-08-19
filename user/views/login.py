from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from user.serializers.login import LoginReqSerializer, LoginResSerializer


User = get_user_model()


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        req_ser = LoginReqSerializer(data=request.data)
        req_ser.is_valid(raise_exception=True)

        username = req_ser.validated_data['username']

        user = User.objects.filter(username=username).first()
        if not user:
            user = User.objects.create(username=username)

        res_ser = LoginResSerializer(instance=user)
        return Response(res_ser.data)
