from django.db import models
from django.contrib.auth import get_user_model

from ._common import TimeStamp

User = get_user_model()


class Group(TimeStamp):
    name = models.CharField(max_length=150)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='groups_owned')
    members = models.ManyToManyField(User, related_name='groups_joined')

    def is_owner(self, user):
        return user == self.owner
