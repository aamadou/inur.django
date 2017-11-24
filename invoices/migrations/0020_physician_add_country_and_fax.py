# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-11-24 13:30
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('invoices', '0019_invoice_item_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='physician',
            name='country',
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
        migrations.AddField(
            model_name='physician',
            name='fax_number',
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
    ]