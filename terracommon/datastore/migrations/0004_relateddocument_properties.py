# Generated by Django 2.0.13 on 2019-07-15 12:10

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('datastore', '0003_auto_20181120_1059'),
    ]

    operations = [
        migrations.AddField(
            model_name='relateddocument',
            name='properties',
            field=django.contrib.postgres.fields.jsonb.JSONField(default=dict),
        ),
    ]