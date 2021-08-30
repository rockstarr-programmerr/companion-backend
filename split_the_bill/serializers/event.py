from django.utils.translation import gettext as _
from rest_framework import serializers

from split_the_bill.models import Event

from ._common import PkField
from .fund import FundSerializer
from .user import UserSerializer


class EventSerializer(serializers.HyperlinkedModelSerializer):
    creator = UserSerializer(read_only=True)
    members = UserSerializer(many=True, read_only=True)
    fund = FundSerializer(read_only=True)

    class Meta:
        model = Event
        fields = ['url', 'pk', 'name', 'creator', 'members', 'fund', 'create_time']


class _PkListField(serializers.ListField):
    child = PkField()


class AddMembersSerializer(serializers.Serializer):
    member_pks = _PkListField(allow_empty=False, max_length=100)


class RemoveMembersSerializer(serializers.Serializer):
    member_pks = _PkListField(allow_empty=False, max_length=100)

    def validate_member_pks(self, pks):
        request = self.context['request']
        if request.user.pk in pks:
            raise serializers.ValidationError(_('Cannot remove yourself from event.'))
        return pks
