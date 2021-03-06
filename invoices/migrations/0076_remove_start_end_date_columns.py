# Generated by Django 2.2.8 on 2019-12-13 16:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('invoices', '0075_auto_20191128_1716'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='simplifiedtimesheet',
            name='end_date',
        ),
        migrations.RemoveField(
            model_name='simplifiedtimesheet',
            name='start_date',
        ),
        migrations.AlterField(
            model_name='simplifiedtimesheet',
            name='time_sheet_month',
            field=models.PositiveSmallIntegerField(choices=[(1, 'Janvier'), (2, 'Février'), (3, 'Mars'), (4, 'Avril'), (5, 'Mai'), (6, 'Juin'), (7, 'Juillet'), (8, 'Août'), (9, 'Septembre'), (10, 'Octobre'), (11, 'Novembre'), (12, 'Décembre')], default=12, max_length=2),
        ),
    ]
