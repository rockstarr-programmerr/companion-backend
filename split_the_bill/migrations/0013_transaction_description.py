# Generated by Django 3.2.7 on 2021-10-25 14:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('split_the_bill', '0012_auto_20211008_2200'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='description',
            field=models.TextField(blank=True),
        ),
    ]
