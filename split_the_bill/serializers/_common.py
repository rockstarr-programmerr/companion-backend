from rest_framework import serializers


class PkField(serializers.IntegerField):
    def __init__(self, *args, **kwargs):
        kwargs['min_value'] = 1
        super().__init__(*args, **kwargs)
