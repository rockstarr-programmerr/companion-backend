from django.utils.translation import gettext as _
from rest_framework import serializers
from rest_framework.fields import ListField
from rest_framework.reverse import reverse

from split_the_bill.models import Event
from split_the_bill.utils.url import update_url_params
from user.serializers.user import UserSerializer

from ._common import PkField


class EventSerializer(serializers.HyperlinkedModelSerializer):
    creator = UserSerializer(read_only=True)
    members = UserSerializer(many=True, read_only=True)
    transactions_url = serializers.SerializerMethodField(read_only=True)
    extra_action_urls = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Event
        fields = [
            'url', 'pk', 'name',
            'creator', 'members', 'create_time',
            'transactions_url', 'extra_action_urls',
        ]

    def get_transactions_url(self, transaction):
        url = reverse('transaction-list', request=self.context['request'])
        params = {'event': transaction.pk}
        return update_url_params(url, params)

    def get_extra_action_urls(self, transaction):
        kwargs = {
            'kwargs': {'pk': transaction.pk},
            'request': self.context['request'],
        }
        return {
            'add_members': reverse('event-add-members', **kwargs),
            'remove_members': reverse('event-remove-members', **kwargs),
        }


class AddMembersSerializer(serializers.Serializer):
    member_usernames = ListField(child=serializers.CharField(), allow_empty=False, max_length=100)


class RemoveMembersSerializer(serializers.Serializer):
    member_pks = ListField(child=PkField(), allow_empty=False, max_length=100)

    def validate_member_pks(self, pks):
        request = self.context['request']
        if request.user.pk in pks:
            raise serializers.ValidationError(_('Cannot remove yourself from event.'))
        return pks
