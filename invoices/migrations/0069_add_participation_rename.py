# Generated by Django 2.2.7 on 2019-11-14 14:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('invoices', '0068_add_participation'),
    ]

    operations = [
        migrations.RenameField(
            model_name='carecode',
            old_name='participation',
            new_name='contribution_undue',
        ),
    ]
