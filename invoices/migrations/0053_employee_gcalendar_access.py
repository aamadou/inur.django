# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-12-27 13:58
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('invoices', '0052_prestation_at_home_paired_upd'),
    ]

    operations = [
        migrations.AddField(
            model_name='employee',
            name='has_gcalendar_access',
            field=models.BooleanField(default=False, verbose_name=b"Allow access to Prestations' calendar"),
        ),
    ]
