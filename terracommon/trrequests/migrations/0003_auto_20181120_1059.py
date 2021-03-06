# Generated by Django 2.0.9 on 2018-11-20 10:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('trrequests', '0002_auto_20180824_1017'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='comment',
            options={'ordering': ['id']},
        ),
        migrations.AlterModelOptions(
            name='userrequest',
            options={'ordering': ['id'], 'permissions': (('can_create_requests', 'Is able to create a new requests'), ('can_read_self_requests', 'Is able to get own requests'), ('can_read_all_requests', 'Is able to get all requests'), ('can_comment_requests', 'Is able to comment an user request'), ('can_internal_comment_requests', 'Is able to add comments not visible by users'), ('can_read_comment_requests', 'Is allowed to read only non-internal comments'), ('can_change_state_requests', 'Is authorized to change the request state'), ('can_download_all_pdf', 'Is able to download a pdf document'))},
        ),
    ]
