# Generated by Django 2.0.5 on 2018-06-22 14:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('trrequests', '0011_auto_20180619_1458'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='organization',
            name='owner',
        ),
        migrations.RemoveField(
            model_name='userrequest',
            name='organization',
        ),
        migrations.DeleteModel(
            name='Organization',
        ),
    ]