from rest_framework import serializers
from django.utils.translation import gettext as _

from split_the_bill.models import Trip
from .user import UserSerializer


class TripSerializer(serializers.ModelSerializer):
    creator = UserSerializer(read_only=True)
    members = UserSerializer(many=True, read_only=True)

    class Meta:
        model = Trip
        fields = ['pk', 'name', 'creator', 'members', 'create_time']
