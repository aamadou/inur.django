# Generated by Django 3.0.7 on 2020-06-28 20:48

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django_currentuser.db.models.fields
import django_currentuser.middleware
import gdstorage.storage
import invoices.models
import invoices.storages
import invoices.validators.validators


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('invoices', '0080_2020_import_cns_prices_'),
    ]

    operations = [
        migrations.CreateModel(
            name='EventType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, verbose_name='Descriptive Name')),
                ('to_be_generated', models.BooleanField(default=False, help_text='If checked, this events types will be generated automatically', verbose_name='To be generated')),
            ],
            options={
                'verbose_name': 'Event -> Type',
                'verbose_name_plural': 'Event -> Types',
                'ordering': ['-id'],
            },
        ),
        migrations.AlterModelOptions(
            name='hospitalization',
            options={'ordering': ['-id']},
        ),
        migrations.AlterModelOptions(
            name='invoiceitem',
            options={'ordering': ['-id'], 'verbose_name': "Mémoire d'honoraire", 'verbose_name_plural': "Mémoires d'honoraire"},
        ),
        migrations.AlterModelOptions(
            name='jobposition',
            options={'ordering': ['-id']},
        ),
        migrations.AlterModelOptions(
            name='medicalprescription',
            options={'ordering': ['-id']},
        ),
        migrations.AlterModelOptions(
            name='patient',
            options={'ordering': ['-id']},
        ),
        migrations.AlterModelOptions(
            name='physician',
            options={'ordering': ['-id']},
        ),
        migrations.AlterModelOptions(
            name='prestation',
            options={'ordering': ['-date']},
        ),
        migrations.AlterModelOptions(
            name='timesheet',
            options={'ordering': ['-id']},
        ),
        migrations.AlterModelOptions(
            name='timesheettask',
            options={'ordering': ['-id']},
        ),
        migrations.AlterField(
            model_name='holidayrequest',
            name='employee',
            field=django_currentuser.db.models.fields.CurrentUserField(default=django_currentuser.middleware.get_current_authenticated_user, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='holidayrequest',
            name='reason',
            field=models.PositiveSmallIntegerField(choices=[(1, 'Congés'), (2, 'Maladie'), (3, 'Formation'), (4, 'Desiderata')]),
        ),
        migrations.AlterField(
            model_name='invoiceitem',
            name='accident_id',
            field=models.CharField(blank=True, help_text="Numéro d'accident est facultatif", max_length=30, null=True),
        ),
        migrations.AlterField(
            model_name='invoiceitem',
            name='is_private',
            field=models.BooleanField(default=False, help_text='Seuls les patients qui ne disposent pas de la prise en charge CNS seront recherchés dans le champ Patient (privé)', verbose_name='Facture pour patient non pris en charge par CNS'),
        ),
        migrations.AlterField(
            model_name='invoiceitem',
            name='medical_prescription',
            field=models.ForeignKey(blank=True, help_text='Please choose a Medical Prescription', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='invoice_items', to='invoices.MedicalPrescription'),
        ),
        migrations.AlterField(
            model_name='invoiceitem',
            name='patient',
            field=models.ForeignKey(help_text='choisir parmi les patients en entrant quelques lettres de son nom ou prénom', on_delete=django.db.models.deletion.CASCADE, related_name='invoice_items', to='invoices.Patient'),
        ),
        migrations.AlterField(
            model_name='invoiceitembatch',
            name='file',
            field=models.FileField(blank=True, storage=gdstorage.storage.GoogleDriveStorage(), upload_to=invoices.models.invoiceitembatch_filename),
        ),
        migrations.AlterField(
            model_name='medicalprescription',
            name='file',
            field=models.ImageField(blank=True, storage=invoices.storages.CustomizedGoogleDriveStorage(), upload_to=invoices.models.update_medical_prescription_filename, validators=[invoices.models.validate_image]),
        ),
        migrations.AlterField(
            model_name='patient',
            name='code_sn',
            field=models.CharField(max_length=30, validators=[invoices.validators.validators.MyRegexValidator(code='invalid_code_sn', message='Premier chiffre (1 à 2) suivi de 12 chiffres (0 à 9)', regex='^[12]\\d{12}')]),
        ),
        migrations.AlterField(
            model_name='prestation',
            name='employee',
            field=models.ForeignKey(blank=True, default='auth.User', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='prestations', to='invoices.Employee'),
        ),
        migrations.AlterField(
            model_name='publicholidaycalendar',
            name='calendar_year',
            field=models.PositiveIntegerField(default=2020),
        ),
        migrations.AlterField(
            model_name='simplifiedtimesheet',
            name='time_sheet_month',
            field=models.PositiveSmallIntegerField(choices=[(1, 'Janvier'), (2, 'Février'), (3, 'Mars'), (4, 'Avril'), (5, 'Mai'), (6, 'Juin'), (7, 'Juillet'), (8, 'Août'), (9, 'Septembre'), (10, 'Octobre'), (11, 'Novembre'), (12, 'Décembre')], default=6),
        ),
        migrations.AlterField(
            model_name='simplifiedtimesheet',
            name='time_sheet_year',
            field=models.PositiveIntegerField(default=2020),
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('day', models.DateField(help_text='Event day', verbose_name='Event day')),
                ('state', models.PositiveSmallIntegerField(choices=[(1, 'Waiting for validation'), (2, 'Valid'), (3, 'Done'), (4, 'Ignored')])),
                ('notes', models.TextField(blank=True, help_text='Notes', null=True, verbose_name='Notes')),
                ('event_type', models.ForeignKey(blank=True, help_text='Event type', null=True, on_delete=django.db.models.deletion.SET_NULL, to='invoices.EventType')),
                ('patient', models.ForeignKey(blank=True, help_text='Please select a patient', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='event_link_to_patient', to='invoices.Patient')),
            ],
            options={
                'verbose_name': 'Event',
                'verbose_name_plural': 'Events',
            },
        ),
    ]
