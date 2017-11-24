# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-11-22 18:53
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('invoices', '0017_invoiceitem_add_uniqueness_to_invoice_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='prestation',
            name='employee',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='prestations', to='invoices.Employee'),
        ),
        migrations.AlterField(
            model_name='invoiceitem',
            name='patient_invoice_date',
            field=models.DateField(verbose_name=b'Date envoi au patient'),
        ),
    ]