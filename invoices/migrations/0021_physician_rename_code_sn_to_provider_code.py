# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-11-24 13:30
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('invoices', '0020_physician_add_country_and_fax'),
    ]

    operations = [
        migrations.RenameField(
            model_name='physician',
            old_name='code_sn',
            new_name='provider_code',
        ),
    ]