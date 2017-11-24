# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-11-21 12:40
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('invoices', '0015_patient_rename_field_to_is_private'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invoiceitem',
            name='patient',
            field=models.ForeignKey(help_text=b'choisir parmi ces patients pour le mois precedent', on_delete=django.db.models.deletion.CASCADE, related_name='invoice_items', to='invoices.Patient'),
        ),
        migrations.AlterField(
            model_name='invoiceitem',
            name='physician',
            field=models.ForeignKey(blank=True, help_text=b'Please chose the physican who is givng the medical prescription', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='invoice_items', to='invoices.Physician'),
        ),
        migrations.AlterField(
            model_name='prestation',
            name='carecode',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='prestations', to='invoices.CareCode'),
        ),
        migrations.AlterField(
            model_name='prestation',
            name='invoice_item',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='prestations', to='invoices.InvoiceItem'),
        ),
    ]