import secrets
import uuid

import qrcode
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from rest_framework.generics import get_object_or_404
from rest_framework.reverse import reverse

from split_the_bill.utils.url import update_url_params

from ._common import TimeStamp
from .event_invitation import EventInvitation

User = get_user_model()


class Event(TimeStamp):
    name = models.CharField(max_length=150)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='events_created')
    members = models.ManyToManyField(User, related_name='events_participated')
    invited_users = models.ManyToManyField(User, through=EventInvitation, related_name='events_invited_to')
    qr_code = models.ImageField(upload_to='split_the_bill/event/qr_code/%Y/%m')
    join_token = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return f'{self.name} | {self.creator}'

    def save(self, *args, **kwargs):
        if not self.join_token:
            self.join_token = self.create_join_token()
        return super().save(*args, **kwargs)

    def is_creator(self, user):
        return user == self.creator

    def invite_members_by_emails(self, emails):
        users = User.objects.filter(email__in=emails)
        self.invited_users.add(*users)

    def cancel_invite_members_by_emails(self, emails):
        users = User.objects.filter(email__in=emails)
        self.invited_users.remove(*users)

    def create_qr_code(self, request, reset_token=False):
        if reset_token:
            self.join_token = self.create_join_token()
            self.qr_code.delete(save=False)

        join_url = reverse('event-join-with-qr', request=request)
        join_url = update_url_params(join_url, {'token': self.join_token})
        qr_code = qrcode.make(data=join_url)

        random_img_name = uuid.uuid4().hex
        img_name = f'{random_img_name}.png'
        filename = self.qr_code.field.generate_filename(self, img_name)
        path = settings.MEDIA_ROOT / filename
        qr_code.save(path)

        self.qr_code = filename
        self.save()

    @staticmethod
    def create_join_token():
        return secrets.token_urlsafe(nbytes=10)

    @classmethod
    def join_with_qr_code(cls, user, token):
        event = get_object_or_404(cls, join_token=token)
        event.members.add(user)
