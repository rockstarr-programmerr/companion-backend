from rest_framework import serializers

from split_the_bill.models import Fund


class FundSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fund
        fields = ['balance']
