from rest_framework import serializers
from django.utils.translation import gettext as _

from split_the_bill.models import Group
from .user import UserSerializer


class GroupSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    members = UserSerializer(many=True, read_only=True)

    class Meta:
        model = Group
        fields = ['pk', 'name', 'owner', 'members', 'create_time']

    def validate_name(self, name):
        owner = self.context['request'].user
        if Group.name_not_unique_for_owner(owner, name):
            raise serializers.ValidationError(
                detail=_('This group already exists.'),
                code='unique_together'
            )
        return name
