from django.db import models


class Fund(models.Model):
    event = models.OneToOneField('Event', on_delete=models.CASCADE)
    balance = models.IntegerField(default=0)
