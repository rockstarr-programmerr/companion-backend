from django.utils.translation import gettext as _
from rest_framework import serializers
from rest_framework.reverse import reverse

from split_the_bill.models import Event
from split_the_bill.utils.url import update_url_params

from ._common import PkField
from .user import UserSerializer


class EventSerializer(serializers.HyperlinkedModelSerializer):
    creator = UserSerializer(read_only=True)
    members = UserSerializer(many=True, read_only=True)
    transactions_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Event
        fields = ['url', 'pk', 'name', 'creator', 'members', 'create_time', 'transactions_url']

    def get_transactions_url(self, transaction):
        url = reverse('transaction-list', request=self.context['request'])
        params = {'event': transaction.pk}
        return update_url_params(url, params)


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
