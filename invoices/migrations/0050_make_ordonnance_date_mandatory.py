# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-12-18 21:54
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('invoices', '0049_merge_20171218_1528'),
    ]

    operations = [
        migrations.AlterField(
            model_name='medicalprescription',
            name='date',
            field=models.DateField(verbose_name=b'Date ordonnance'),
        ),
    ]