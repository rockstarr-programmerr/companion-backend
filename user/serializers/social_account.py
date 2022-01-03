from rest_framework import serializers
from ..models import FacebookDataDeletionRequest


class CallbackViewSerializer(serializers.Serializer):
    access_token = serializers.CharField()
    refresh_token = serializers.CharField(required=False)
    expires_in = serializers.IntegerField(required=False, help_text='Number of seconds.')

    def to_representation(self, instance):
        serializer = CallbackViewResponseSerializer(instance=instance, context=self.context)
        return serializer.data


class CallbackViewResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()


class FbDataDeletionStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = FacebookDataDeletionRequest
        fields = ['confirmation_code', 'status', 'issued_at', 'expires']
