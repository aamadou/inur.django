# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-12-05 15:47
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('invoices', '0035_prestation_at_home'),
    ]

    operations = [
        migrations.AlterField(
            model_name='prestation',
            name='employee',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='prestations', to='invoices.Employee'),
        ),
    ]