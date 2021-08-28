# Generated by Django 3.2.6 on 2021-08-28 14:29

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('split_the_bill', '0002_alter_group_unique_together'),
    ]

    operations = [
        migrations.CreateModel(
            name='Trip',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True)),
                ('update_time', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=150)),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='trips_created', to=settings.AUTH_USER_MODEL)),
                ('members', models.ManyToManyField(related_name='trips_participated', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
