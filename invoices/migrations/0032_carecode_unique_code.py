# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-12-01 09:50
from __future__ import unicode_literals

from django.db import migrations, models


def update_not_unique_codes(apps, schema_editor):
    CareCodeModel = apps.get_model('invoices', 'CareCode')
    for carecode in CareCodeModel.objects.all():
        duplicates_queryset = CareCodeModel.objects.filter(code=carecode.code)
        for index, duplicate in enumerate(duplicates_queryset):
            new_code = duplicate.code + '_' + format(index, '02d')
            if 0 == index:
                new_code = duplicate.code

            duplicate.code = new_code
            duplicate.save()


class Migration(migrations.Migration):

    dependencies = [
        ('invoices', '0031_validity_dates_rename_relation'),
    ]

    operations = [
        migrations.RunSQL('SET CONSTRAINTS ALL IMMEDIATE',
                          reverse_sql=migrations.RunSQL.noop),
        migrations.RunPython(update_not_unique_codes),
        migrations.RunSQL(migrations.RunSQL.noop,
                          reverse_sql='SET CONSTRAINTS ALL IMMEDIATE'),
        migrations.AlterField(
            model_name='carecode',
            name='code',
            field=models.CharField(max_length=30, unique=True),
        ),
    ]
