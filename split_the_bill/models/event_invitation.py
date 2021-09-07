from django.contrib.auth import get_user_model
from django.db import models

from ._common import TimeStamp

User = get_user_model()


class EventInvitation(TimeStamp):
    class Statuses(models.TextChoices):
        PENDING = 'pending'
        ACCEPTED = 'accepted'
        DECLINED = 'declined'

    event = models.ForeignKey('Event', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=8, choices=Statuses.choices, default=Statuses.PENDING)

    class Meta:
        unique_together = ['event', 'user']

    def is_pending(self):
        return self.status == self.Statuses.PENDING

    def is_accepted(self):
        return self.status == self.Statuses.ACCEPTED

    def is_declined(self):
        return self.status == self.Statuses.DECLINED
