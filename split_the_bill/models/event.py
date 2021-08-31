from django.db import models
from django.contrib.auth import get_user_model

from ._common import TimeStamp

User = get_user_model()


class Event(TimeStamp):
    name = models.CharField(max_length=150)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='events_created')
    members = models.ManyToManyField(User, related_name='events_participated')

    def is_creator(self, user):
        return user == self.creator
