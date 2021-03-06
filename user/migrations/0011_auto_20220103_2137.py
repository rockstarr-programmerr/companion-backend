# Generated by Django 3.2.7 on 2022-01-03 14:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0010_facebookdatadeletionrequest'),
    ]

    operations = [
        migrations.AlterField(
            model_name='facebookdatadeletionrequest',
            name='confirmation_code',
            field=models.CharField(max_length=255, unique=True),
        ),
        migrations.AlterField(
            model_name='facebookdatadeletionrequest',
            name='expires',
            field=models.DateTimeField(),
        ),
        migrations.AlterField(
            model_name='facebookdatadeletionrequest',
            name='issued_at',
            field=models.DateTimeField(),
        ),
    ]
