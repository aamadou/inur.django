# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-12-01 15:50
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('invoices', '0034_carecode_exclusive_care_codes'),
    ]

    operations = [
        migrations.AddField(
            model_name='prestation',
            name='at_home',
            field=models.BooleanField(default=False),
        ),
    ]
