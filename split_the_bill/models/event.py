from django.db import models
from django.contrib.auth import get_user_model

from ._common import TimeStamp
from .event_invitation import EventInvitation

User = get_user_model()


class Event(TimeStamp):
    name = models.CharField(max_length=150)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='events_created')
    members = models.ManyToManyField(User, related_name='events_participated')
    invitations = models.ManyToManyField(User, through=EventInvitation, related_name='events_invited_to')

    def __str__(self):
        return f'{self.name} | {self.creator}'

    def is_creator(self, user):
        return user == self.creator

    def add_members_by_usernames(self, usernames):
        members = User.objects.filter(username__in=usernames)
        self.members.add(*members)
