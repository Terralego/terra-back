# Generated by Django 2.0.9 on 2018-11-20 10:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0002_eventhandler_priority'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='eventhandler',
            options={'ordering': ['id']},
        ),
    ]
