from rest_framework import serializers


class PkField(serializers.IntegerField):
    min_value = 1
