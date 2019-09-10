# Generated by Django 2.0.13 on 2019-07-15 12:40

from django.db import migrations
import django.db.models.expressions


class Migration(migrations.Migration):

    dependencies = [
        ('tropp', '0005_remove_document'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='picture',
            options={'get_latest_by': 'date', 'ordering': [django.db.models.expressions.OrderBy(django.db.models.expressions.F('date'), descending=True, nulls_last=True)], 'permissions': (('change_state_picture', 'Is able to change the picture state'),)},
        ),
    ]