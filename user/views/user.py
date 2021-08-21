from django.contrib.auth import get_user_model

from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status

from user.serializers.user import UserInfoSerializer, RegisterReqSerializer, RegisterResSerializer


User = get_user_model()


class UserViewSet(GenericViewSet):
    serializer_class = UserInfoSerializer

    def get_queryset(self):
        return User.objects.filter(pk=self.request.user.pk)

    @action(detail=False, methods=['GET'], url_path='get-my-info')
    def get_info(self, request):
        serializer = self.get_serializer_class()(instance=request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['POST', 'PUT', 'PATCH'], url_path='update-my-info')
    def update_info(self, request):
        serializer = self.get_serializer_class()(data=request.data)
        serializer.is_valid(raise_exception=True)

        for key, value in serializer.validated_data.items():
            setattr(request.user, key, value)
        request.user.save()

        serializer = self.get_serializer_class()(instance=request.user)
        return Response(serializer.data)


class Register(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterReqSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data['username']
        email = serializer.validated_data.get('email')
        password = serializer.validated_data['password']

        user = User.objects.create_user(username, email=email, password=password)

        serializer = RegisterResSerializer(instance=user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
