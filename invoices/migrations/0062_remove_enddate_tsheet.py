# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-06-20 14:33
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('invoices', '0061_employee_drive_access_descr'),
    ]

    operations = [
        migrations.AlterField(
            model_name='timesheetdetail',
            name='end_date',
            field=models.TimeField(verbose_name=b'Heure fin'),
        ),
        migrations.AlterField(
            model_name='timesheetdetail',
            name='start_date',
            field=models.DateTimeField(verbose_name=b'Date'),
        ),
    ]