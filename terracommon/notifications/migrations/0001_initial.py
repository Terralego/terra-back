# Generated by Django 2.0.8 on 2018-08-17 08:01

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserNotifications',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('read', models.BooleanField(default=False)),
                ('level', models.CharField(choices=[('DEBUG', 'Debug'), ('INFO', 'Information'), ('SUCCESS', 'Succès'), ('WARNING', 'Avertissement'), ('ERROR', 'Erreur')], max_length=255)),
                ('event_code', models.CharField(max_length=255)),
                ('message', models.TextField(blank=True)),
                ('identifier', models.IntegerField()),
                ('uuid', models.UUIDField(null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='notifications', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
