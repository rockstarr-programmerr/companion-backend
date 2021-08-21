from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class UserInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email']

class RegisterReqSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'password']

class RegisterResSerializer(UserInfoSerializer):
    """
    After register successfull, I should get my info just like in 'get-my-info' endpoint
    """
