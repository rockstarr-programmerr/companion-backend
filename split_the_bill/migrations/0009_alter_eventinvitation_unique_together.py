# Generated by Django 3.2.6 on 2021-09-07 15:04

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('split_the_bill', '0008_auto_20210907_2149'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='eventinvitation',
            unique_together={('event', 'user')},
        ),
    ]