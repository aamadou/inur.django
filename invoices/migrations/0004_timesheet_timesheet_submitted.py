# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-03-08 10:36
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('invoices', '0003_auto_20160224_1649'),
    ]

    operations = [
        migrations.AddField(
            model_name='timesheet',
            name='timesheet_submitted',
            field=models.BooleanField(default=False, help_text=b"Cochez si vous avez fini d'encoder votre fiche"),
        ),
    ]
