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
