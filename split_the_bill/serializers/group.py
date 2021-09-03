from rest_framework import serializers
from django.utils.translation import gettext as _

from split_the_bill.models import Group
from user.serializers.user import UserSerializer


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    owner = UserSerializer(read_only=True)
    members = UserSerializer(many=True, read_only=True)

    class Meta:
        model = Group
        fields = ['url', 'pk', 'name', 'owner', 'members', 'create_time']

    def validate_name(self, name):
        request = self.context['request']
        owner = request.user
        groups = Group.get_groups_by_owner_and_name(owner, name)
        error = False

        if request.method in ('PUT', 'PATCH'):
            pk = request.parser_context['kwargs']['pk']
            group = groups.first()
            if group:
                error = not Group.is_same_pk(group.pk, pk)
        else:
            error = groups.exists()

        if error:
            raise serializers.ValidationError(
                detail=_('This group already exists.'),
                code='unique_together'
            )

        return name
