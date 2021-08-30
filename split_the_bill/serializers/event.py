from django.http import request
from rest_framework import serializers
from django.utils.translation import gettext as _

from split_the_bill.models import Event
from .user import UserSerializer


class EventSerializer(serializers.HyperlinkedModelSerializer):
    creator = UserSerializer(read_only=True)
    members = UserSerializer(many=True, read_only=True)

    class Meta:
        model = Event
        fields = ['url', 'pk', 'name', 'creator', 'members', 'create_time']


class _PkListField(serializers.ListField):
    child = serializers.IntegerField(min_value=1)


class AddMembersSerializer(serializers.Serializer):
    member_pks = _PkListField(allow_empty=False, max_length=100)


class RemoveMembersSerializer(serializers.Serializer):
    member_pks = _PkListField(allow_empty=False, max_length=100)

    def validate_member_pks(self, pks):
        request = self.context['request']
        if request.user.pk in pks:
            raise serializers.ValidationError(_('Cannot remove yourself from event.'))
        return pks
