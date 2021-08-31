from rest_framework import serializers
from django.utils.translation import gettext as _


class PkField(serializers.IntegerField):
    def __init__(self, *args, **kwargs):
        kwargs['min_value'] = 1
        super().__init__(*args, **kwargs)


class CustomChoiceField(serializers.ChoiceField):
    """
    Choice field with more descriptive error message
    """
    def __init__(self, choices, **kwargs):
        if not 'error_messages' in kwargs:
            valid_choices = ', '.join(f'"{choice[0]}"' for choice in choices)
            kwargs['error_messages'] = {
                'invalid_choice': _(
                    '"{input}" is not a valid choice. Valid choices are %s.'
                ) % valid_choices
            }
        super().__init__(choices, **kwargs)
