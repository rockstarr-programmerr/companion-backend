from rest_framework import serializers

from split_the_bill.models import Group
from .user import UserSerializer


class GroupSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    members = UserSerializer(many=True, read_only=True)

    class Meta:
        model = Group
        fields = ['pk', 'name', 'owner', 'members', 'create_time']
