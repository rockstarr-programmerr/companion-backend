from django.contrib.auth import get_user_model
from rest_framework import serializers


User = get_user_model()


class LoginReqSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)


class LoginResSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'pk',
            'username',
        ]
