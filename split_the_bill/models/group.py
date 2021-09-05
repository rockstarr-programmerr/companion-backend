from django.db import models
from django.contrib.auth import get_user_model

from ._common import TimeStamp

User = get_user_model()


class Group(TimeStamp):
    name = models.CharField(max_length=150)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='groups_owned')
    members = models.ManyToManyField(User, related_name='groups_joined')

    class Meta:
        unique_together = ['name', 'owner']

    def __str__(self):
        return f'{self.name} | {self.owner}'

    def is_owner(self, user):
        return user == self.owner

    @staticmethod
    def is_same_pk(pk1, pk2):
        return str(pk1) == str(pk2)

    @classmethod
    def get_groups_by_owner_and_name(cls, owner, name):
        return cls.objects.filter(owner=owner, name=name)
