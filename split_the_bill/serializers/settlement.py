from rest_framework import serializers

from split_the_bill.models import Settlement
from user.serializers.user import UserSerializer


class SettlementSerializer(serializers.HyperlinkedModelSerializer):
    from_user = UserSerializer()
    to_user = UserSerializer()

    class Meta:
        model = Settlement
        fields = [
            'url', 'pk', 'event',
            'from_user', 'to_user',
            'is_paid', 'amount',
        ]
        read_only_fields = [
            'event', 'from_user',
            'to_user', 'amount'
        ]
