from rest_framework import serializers


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
