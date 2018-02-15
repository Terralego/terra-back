# Generated by Django 2.0.2 on 2018-02-15 16:27

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('terra', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='FeatureRelation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('properties', django.contrib.postgres.fields.jsonb.JSONField()),
                ('destination', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='relations_as_destination', to='terra.Feature')),
                ('origin', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='relations_as_origin', to='terra.Feature')),
            ],
        ),
    ]
