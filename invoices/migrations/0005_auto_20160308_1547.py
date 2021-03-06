# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-03-08 14:47
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('invoices', '0004_timesheet_timesheet_submitted'),
    ]

    operations = [
        migrations.AddField(
            model_name='timesheetdetail',
            name='other',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='timesheet',
            name='end_date',
            field=models.DateField(verbose_name=b'Date fin'),
        ),
        migrations.AlterField(
            model_name='timesheet',
            name='other_details',
            field=models.TextField(blank=True, max_length=100, null=True, verbose_name=b'Autres details'),
        ),
        migrations.AlterField(
            model_name='timesheet',
            name='start_date',
            field=models.DateField(verbose_name=b'Date debut'),
        ),
        migrations.AlterField(
            model_name='timesheet',
            name='submitted_date',
            field=models.DateTimeField(blank=True, null=True, verbose_name=b"Date d'envoi"),
        ),
    ]
