# -*- coding: utf-8 -*-
import logging
from typing import Optional, Dict, Any

import pytz
import os
from copy import deepcopy
from datetime import datetime

from django.conf import settings
from django.core.exceptions import ValidationError
# from django.core.files.storage import FileSystemStorage
from django.db import models
from django.db.models import Q, IntegerField, Max
from django.db.models.functions import Cast
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.utils.safestring import mark_safe
from django_countries.fields import CountryField
from gdstorage.storage import GoogleDriveStorage

from invoices.invoiceitem_pdf import InvoiceItemBatchPdf
from invoices.gcalendar import PrestationGoogleCalendar
from invoices.managers import InvoiceItemBatchManager

from django.utils.timezone import now

from invoices.storages import CustomizedGoogleDriveStorage
from constance import config

from invoices.employee import Employee
from invoices.validators.validators import MyRegexValidator

prestation_gcalendar = PrestationGoogleCalendar()
gd_storage: CustomizedGoogleDriveStorage = CustomizedGoogleDriveStorage()
batch_gd_storage: GoogleDriveStorage = GoogleDriveStorage()
# else:
#    gd_storage = FileSystemStorage()

logger = logging.getLogger(__name__)


class CareCode(models.Model):
    class Meta:
        ordering = ['-id']

    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=50)
    description = models.TextField(max_length=400)
    reimbursed = models.BooleanField("Prise en charge par CNS", default=True)
    contribution_undue = models.BooleanField(u"Participation forfaitaire non dûe",
                                             help_text=u"Si vous sélectionnez cette option la participation de 12% ne "
                                                       u"sera pas déduite de cette prestation",
                                             default=False)
    exclusive_care_codes = models.ManyToManyField("self", blank=True)

    @property
    def current_gross_amount(self):
        return self.gross_amount(datetime.date.today())

    def gross_amount(self, date):
        for v in self.validity_dates.all():
            if date.date() >= v.start_date:
                if v.end_date is None:
                    return v.gross_amount
                elif date.date() <= v.end_date:
                    return v.gross_amount
        return 0

    def net_amount(self, date, private_patient, participation_statutaire):
        if not private_patient:
            if self.reimbursed and not self.contribution_undue:
                return round(((self.gross_amount(date) * 88) / 100), 2) + self._fin_part(date, participation_statutaire)
            else:
                return self.gross_amount(date)
        else:
            return 0

    def _fin_part(self, date, participation_statutaire):
        "Returns the financial participation of the client"
        if participation_statutaire:
            return 0
        # round to only two decimals
        return round(((self.gross_amount(date) * 12) / 100), 2)

    def __str__(self):
        return '%s:%s' % (self.code, self.name)

    @staticmethod
    def autocomplete_search_fields():
        return 'name', 'code'

    def clean(self, *args, **kwargs):
        super(CareCode, self).clean_fields()
        messages = self.validate(self.id, self.__dict__)
        if messages:
            raise ValidationError(messages)

    @staticmethod
    def validate(instance_id, data):
        result = {}
        result.update(CareCode.validate_combination(data))
        return result

    @staticmethod
    def validate_combination(data):
        messages = {}
        if 'contribution_undue' in data and data['contribution_undue'] is not None:
            is_invalid = data['reimbursed'] is False and data['contribution_undue'] is True
            if is_invalid:
                messages = {'contribution_undue':
                                u'Vous ne pouvez appliquer ce champ que pour les soins remboursés par la CNS'}
        return messages


class ValidityDate(models.Model):
    """
    CareCode cannot have start and end validity dates that overlap.
    Depending on Prestation date, gross_amount that is calculated in Invoice will differ.

    """

    class Meta:
        ordering = ['-id']

    start_date = models.DateField("date debut validite")
    end_date = models.DateField("date fin validite", blank=True, null=True)
    gross_amount = models.DecimalField("montant brut", max_digits=5, decimal_places=2)
    care_code = models.ForeignKey(CareCode
                                  , related_name='validity_dates'
                                  , on_delete=models.CASCADE)

    def __str__(self):
        return 'from %s to %s' % (self.start_date, self.end_date)

    def clean(self, *args, **kwargs):
        exclude = []
        if self.care_code is not None and self.care_code.id is None:
            exclude = ['care_code']

        super(ValidityDate, self).clean_fields(exclude)
        messages = self.validate(self.id, self.__dict__)
        if messages:
            raise ValidationError(messages)

    @staticmethod
    def validate(instance_id, data):
        result = {}
        result.update(ValidityDate.validate_dates(data))

        return result

    @staticmethod
    def validate_dates(data):
        messages = {}
        is_valid = data['end_date'] is None or data['start_date'] <= data['end_date']
        if not is_valid:
            messages = {'end_date': 'End date must be bigger than Start date'}

        return messages


def extract_birth_date(code_sn) -> object:
    stripped_sn_code = code_sn.replace(" ", "")
    if stripped_sn_code is not None and (stripped_sn_code[:4]).isdigit():
        if (stripped_sn_code[4:6]).isdigit() and int(stripped_sn_code[4:6]) < 13:
            if (stripped_sn_code[6:8]).isdigit() and int(stripped_sn_code[6:8]) < 32:
                return datetime.strptime(stripped_sn_code[:8], '%Y%m%d')
    return None


def calculate_age(care_date, code_sn):
    if care_date is None:
        care_date = datetime.now()
    born = extract_birth_date(code_sn)
    if born is not None:
        return care_date.year - born.year - ((care_date.month, care_date.day) < (born.month, born.day))
    return None


# TODO: synchronize patient details with Google contacts
class Patient(models.Model):
    class Meta:
        ordering = ['-id']

    code_sn = models.CharField(max_length=30, validators=[MyRegexValidator(
        regex='^[12]\d{12}',
        message='Premier chiffre (1 à 2) suivi de 12 chiffres (0 à 9)',
        code='invalid_code_sn'
    ),
    ])
    first_name = models.CharField(max_length=30)
    name = models.CharField(max_length=30)
    address = models.TextField(max_length=255)
    zipcode = models.CharField(max_length=10)
    city = models.CharField(max_length=30)
    country = CountryField(blank_label='...', blank=True, null=True)
    phone_number = models.CharField(max_length=30)
    email_address = models.EmailField(default=None, blank=True, null=True)
    participation_statutaire = models.BooleanField(default=False)
    is_private = models.BooleanField(default=False)
    date_of_death = models.DateField(u"Date de décès", default=None, blank=True, null=True)

    @property
    def age(self):
        return self.calculate_age(None)

    @staticmethod
    def autocomplete_search_fields():
        return 'name', 'first_name'

    def __str__(self):  # Python 3: def __str__(self):,
        return '%s %s' % (self.name.strip(), self.first_name.strip())

    def clean(self, *args, **kwargs):
        self.code_sn = self.format_code_sn(self.code_sn)
        super(Patient, self).clean_fields()
        messages = self.validate(self.id, self.__dict__)
        if messages:
            raise ValidationError(messages)

    @staticmethod
    def format_code_sn(code_sn):
        return code_sn.replace(" ", "")

    @staticmethod
    def validate(instance_id, data):
        result = {}
        result.update(Patient.validate_code_sn(instance_id, data))
        result.update(Patient.validate_date_of_death(instance_id, data))
        result.update(Patient.patient_age_validation(data))
        return result

    @staticmethod
    def validate_date_of_death(instance_id, data):
        messages = {}
        if 'date_of_death' in data and data['date_of_death'] is not None:
            if Prestation.objects.filter(date__gte=data['date_of_death'], invoice_item__patient_id=instance_id).count():
                messages = {'date_of_death': 'Prestation for a later date exists'}

            if Hospitalization.objects.filter(end_date__gte=data['date_of_death']).count():
                messages = {'date_of_death': 'Hospitalization that ends later exists'}

        return messages

    @staticmethod
    def validate_code_sn(instance_id, data):
        messages = {}
        if 'is_private' in data and not data['is_private']:
            code_sn = data['code_sn'].replace(" ", "")
            if Patient.objects.filter(code_sn=code_sn).exclude(pk=instance_id).count() > 0:
                messages = {'code_sn': 'Code SN must be unique'}
        return messages

    @staticmethod
    def patient_age_validation(data):
        messages = {}
        patient_age = calculate_age(None, data['code_sn'])
        if 'is_private' in data and not data['is_private']:
            if patient_age is None or patient_age < 1 or patient_age > 120:
                messages = {'code_sn': 'Code SN does not look ok, patient cannot be %d year(s) old' % patient_age}
        return messages

    def calculate_age(self, care_date: object) -> object:
        return calculate_age(care_date, self.code_sn)

    def extract_birth_date(self) -> object:
        return self.extract_birth_date(self.code_sn)

    def clean_name(self):
        return self.cleaned_data['name'].upper()

    def clean_first_name(self):
        return self.cleaned_data['first_name'].capitalize()


class Hospitalization(models.Model):
    class Meta:
        ordering = ['-id']
    start_date = models.DateField(u"Début d'hospitlisation")
    end_date = models.DateField(u"Date de fin")
    description = models.TextField(max_length=50, default=None, blank=True, null=True)
    patient = models.ForeignKey(Patient, related_name='hospitalizations',
                                help_text='Please enter hospitalization dates of the patient',
                                on_delete=models.CASCADE)

    def __str__(self):  # Python 3: def __str__(self):
        return 'From %s to %s for %s' % (self.start_date, self.end_date, self.patient)

    def as_dict(self):
        result = self.__dict__
        if self.patient and self.patient is not None:
            result['patient'] = self.patient

        return result

    def clean(self):
        exclude = []
        if self.patient is not None and self.patient.id is None:
            exclude = ['patient']

        super(Hospitalization, self).clean_fields(exclude)
        messages = self.validate(self.id, self.as_dict())
        if messages:
            raise ValidationError(messages)

    @staticmethod
    def validate(instance_id, data):
        result = {}
        result.update(Hospitalization.validate_dates(data))
        result.update(Hospitalization.validate_prestation(data))
        result.update(Hospitalization.validate_patient_alive(data))

        return result

    @staticmethod
    def validate_dates(data):
        messages = {}
        is_valid = data['end_date'] is None or data['start_date'] <= data['end_date']
        if not is_valid:
            messages = {'end_date': 'End date must be bigger than Start date'}

        return messages

    @staticmethod
    def validate_prestation(data):
        messages = {}
        patient_id = None
        if 'patient' in data:
            patient_id = data['patient'].id
        elif 'patient_id' in data:
            patient_id = data['patient_id']
        else:
            messages = {'patient': 'Please fill Patient field'}

        start_date = datetime.combine(data['start_date'], datetime.min.time()).replace(tzinfo=pytz.utc)
        end_date = datetime.combine(data['end_date'], datetime.max.time()).replace(tzinfo=pytz.utc)

        conflicts_cnt = Prestation.objects.filter(Q(date__range=(start_date, end_date))).filter(
            invoice_item__patient_id=patient_id).count()
        if 0 < conflicts_cnt:
            messages = {'start_date': 'Prestation(s) exist in selected dates range for this Patient'}

        return messages

    @staticmethod
    def validate_date_range(instance_id, data):
        messages = {}
        conflicts_cnt = Hospitalization.objects.filter(
            Q(start_date__range=(data['start_date'], data['end_date'])) |
            Q(end_date__range=(data['start_date'], data['end_date'])) |
            Q(start_date__lte=data['start_date'], end_date__gte=data['start_date']) |
            Q(start_date__lte=data['end_date'], end_date__gte=data['end_date'])
        ).filter(
            patient_id=data['patient'].id).exclude(
            pk=instance_id).count()
        if 0 < conflicts_cnt:
            messages = {'start_date': 'Intersection with other Hospitalizations'}

        return messages

    @staticmethod
    def validate_patient_alive(data):
        messages = {}
        patient = None
        if 'patient' in data:
            patient = data['patient']
        elif 'patient_id' in data:
            patient = Patient.objects.filter(pk=data['patient_id']).get()
        else:
            messages = {'patient': 'Please fill Patient field'}

        date_of_death = patient.date_of_death
        if date_of_death is not None and data['end_date'] >= date_of_death:
            messages = {'end_date': "Hospitalization cannot be later than or include Patient's death date"}

        return messages


# TODO: 1. can maybe be extending common class with Patient ?
# TODO: 2. synchronize physician details with Google contacts
class Physician(models.Model):
    class Meta:
        ordering = ['-id']

    provider_code = models.CharField(max_length=30)
    first_name = models.CharField(max_length=30)
    name = models.CharField(max_length=30)
    address = models.TextField(max_length=30)
    zipcode = models.CharField(max_length=10)
    city = models.CharField(max_length=30)
    country = CountryField(blank_label='...', blank=True, null=True)
    phone_number = models.CharField(max_length=30)
    fax_number = models.CharField(max_length=30, blank=True, null=True)
    email_address = models.EmailField(default=None, blank=True, null=True)

    @staticmethod
    def autocomplete_search_fields():
        return 'name', 'first_name'

    def __str__(self):  # Python 3: def __str__(self):
        return '%s %s' % (self.name.strip(), self.first_name.strip())


def update_medical_prescription_filename(instance, filename):
    file_name, file_extension = os.path.splitext(filename)
    if instance.date is None:
        _current_yr_or_prscr_yr = now().date().strftime('%Y')
    else:
        _current_yr_or_prscr_yr = str(instance.date.year)
    path = os.path.join(CustomizedGoogleDriveStorage.MEDICAL_PRESCRIPTION_FOLDER, _current_yr_or_prscr_yr)
    filename = '%s_%s_%s%s' % (instance.patient.name, instance.patient.first_name, str(instance.date), file_extension)

    return os.path.join(path, filename)


def validate_image(image):
    file_size = image.file.size
    limit_kb = 1024
    if file_size > limit_kb * 1024:
        raise ValidationError("Taille maximale du fichier est %s KO" % limit_kb)


class MedicalPrescription(models.Model):
    class Meta:
        ordering = ['-id']

    prescriptor = models.ForeignKey(Physician, related_name='medical_prescription',
                                    help_text='Please chose the Physician who is giving the medical prescription',
                                    on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, default=None, related_name='medical_prescription_patient',
                                help_text='Please chose the Patient who is receiving the medical prescription',
                                on_delete=models.CASCADE)
    date = models.DateField('Date ordonnance')
    end_date = models.DateField('Date fin des soins', null=True, blank=True)
    file = models.ImageField(storage=gd_storage, blank=True,
                             upload_to=update_medical_prescription_filename,
                             validators=[validate_image])
    _original_file = None

    @property
    def file_description(self):
        return '%s %s %s' % (self.patient.name, self.patient.first_name, str(self.date))

    def __init__(self, *args, **kwargs):
        super(MedicalPrescription, self).__init__(*args, **kwargs)
        self._original_file = self.file

    def clean(self):
        logger.info('clean medical prescription %s' % self)
        exclude = []
        if self.patient is not None and self.patient.id is None:
            exclude = ['patient']

        super(MedicalPrescription, self).clean_fields(exclude)
        messages = self.validate(self.id, self.__dict__)
        if messages:
            raise ValidationError(messages)

    @staticmethod
    def validate(instance_id, data):
        result = {}
        result.update(MedicalPrescription.validate_dates(data))

        return result

    @staticmethod
    def validate_dates(data):
        messages = {}
        is_valid = data['end_date'] is None or data['date'] <= data['end_date']
        if not is_valid:
            messages = {'end_date': 'End date must be bigger than Start date'}

        return messages

    def image_preview(self, max_width=None, max_height=None):
        if max_width is None:
            max_width = '800'
        if max_height is None:
            max_height = '800'
        # used in the admin site model as a "thumbnail"
        link = self.file.storage.get_thumbnail_link(getattr(self.file, 'name', None))
        styles = "max-width: %spx; max-height: %spx;" % (max_width, max_height)
        tag = '<img src="{}" style="{}"/>'.format(link, styles)

        return mark_safe(tag)

    def get_original_file(self):
        return self._original_file

    @staticmethod
    def autocomplete_search_fields():
        return 'date', 'prescriptor__name', 'prescriptor__first_name'

    def __str__(self):
        if bool(self.file):
            return '%s %s (%s) [%s...]' % (
                self.prescriptor.name.strip(), self.prescriptor.first_name.strip(), self.date,
                self.file.name[:5])
        else:
            return '%s %s (%s) sans fichier' % (
                self.prescriptor.name.strip(), self.prescriptor.first_name.strip(), self.date)


@receiver(pre_save, sender=MedicalPrescription, dispatch_uid="medical_prescription_clean_gdrive_pre_save")
def medical_prescription_clean_gdrive_pre_save(sender, instance, **kwargs):
    origin_file = instance.get_original_file()
    if origin_file.name and origin_file != instance.file:
        gd_storage.delete(origin_file.name)


@receiver(post_save, sender=MedicalPrescription, dispatch_uid="medical_prescription_clean_gdrive_post_save")
def medical_prescription_clean_gdrive_post_save(sender, instance, **kwargs):
    if instance.file.name:
        path = instance.file.name
        gd_storage.update_file_description(path, instance.file_description)


@receiver(post_delete, sender=MedicalPrescription, dispatch_uid="medical_prescription_clean_gdrive_post_delete")
def medical_prescription_clean_gdrive_post_delete(sender, instance, **kwargs):
    if instance.file.name:
        gd_storage.delete(instance.file.name)


def get_default_invoice_number():
    default_invoice_number = 0
    max_invoice_number = InvoiceItem.objects.filter(Q(invoice_number__iregex=r'^\d+$')).annotate(
        invoice_number_int=Cast('invoice_number', IntegerField())).aggregate(Max('invoice_number_int'))

    if max_invoice_number['invoice_number_int__max'] is not None:
        default_invoice_number = max_invoice_number['invoice_number_int__max']

    default_invoice_number += 1

    return default_invoice_number


def invoiceitembatch_filename(instance, filename):
    return InvoiceItemBatchPdf.get_path(instance)


class InvoiceItemBatch(models.Model):
    start_date = models.DateField('Invoice batch start date')
    end_date = models.DateField('Invoice batch start date')
    send_date = models.DateField(null=True, blank=True)
    payment_date = models.DateField(null=True, blank=True)
    file = models.FileField(storage=batch_gd_storage, blank=True, upload_to=invoiceitembatch_filename)
    _original_file = None

    # invoices to be corrected
    # total_amount

    def __str__(self):  # Python 3: def __str__(self):
        return 'from %s to %s' % (self.start_date, self.end_date)

    def __init__(self, *args, **kwargs):
        super(InvoiceItemBatch, self).__init__(*args, **kwargs)
        self._original_file = self.file

    def get_original_file(self):
        return self._original_file

    def clean(self):
        exclude = []
        super(InvoiceItemBatch, self).clean_fields(exclude)
        messages = self.validate(self.id, self.__dict__)
        if messages:
            raise ValidationError(messages)

    @staticmethod
    def validate(instance_id, data):
        result = {}
        result.update(Hospitalization.validate_dates(data))

        return result

    @staticmethod
    def validate_dates(data):
        messages = {}
        is_valid = data['end_date'] is None or data['start_date'] <= data['end_date']
        if not is_valid:
            messages = {'end_date': 'End date must be bigger than Start date'}

        return messages


@receiver(pre_save, sender=InvoiceItemBatch, dispatch_uid="invoiceitembatch_pre_save")
def invoiceitembatch_generate_pdf_name(sender, instance, **kwargs):
    instance.file = InvoiceItemBatchPdf.get_filename(instance)
    origin_file = instance.get_original_file()
    if origin_file.name and origin_file != instance.file:
        batch_gd_storage.delete(origin_file.name)


# @receiver(post_save, sender=InvoiceItemBatch, dispatch_uid="invoiceitembatch_post_save")
# def invoiceitembatch_generate_pdf(sender, instance, **kwargs):
#     InvoiceItemBatchManager.update_associated_invoiceitems(instance)
#     file_content = InvoiceItemBatchPdf.get_inmemory_pdf(instance)
#     path = InvoiceItemBatchPdf.get_path(instance)
#     instance._original_file = instance.file
#     batch_gd_storage.save_file(path, file_content)


@receiver(post_delete, sender=InvoiceItemBatch, dispatch_uid="invoiceitembatch_post_delete")
def medical_prescription_clean_gdrive_post_delete(sender, instance, **kwargs):
    if instance.file.name:
        gd_storage.delete(instance.file.name)


class InvoiceItem(models.Model):
    class Meta(object):
        ordering = ['-id']
        verbose_name = u"Mémoire d'honoraire"
        verbose_name_plural = u"Mémoires d'honoraire"

    PRESTATION_LIMIT_MAX = 20

    invoice_number = models.CharField(max_length=50, unique=True, default=get_default_invoice_number)
    is_private = models.BooleanField('Facture pour patient non pris en charge par CNS',
                                     help_text=u'Seuls les patients qui ne disposent pas de la prise en charge CNS '
                                               u'seront recherchés dans le champ Patient (privé)',
                                     default=False)
    patient = models.ForeignKey(Patient, related_name='invoice_items',
                                help_text=u"choisir parmi les patients en entrant quelques lettres de son nom ou prénom",
                                on_delete=models.CASCADE)
    # subcontractor = models.ForeignKey(Patient, related_name='invoice_subcontractor',
    #                                   help_text=u'Si vous introduisez un sous traitant',
    #                                   on_delete=models.CASCADE, null=True, blank=True)
    accident_id = models.CharField(max_length=30, help_text=u"Numéro d'accident est facultatif", null=True, blank=True)
    accident_date = models.DateField(help_text=u"Date d'accident est facultatif", null=True, blank=True)
    invoice_date = models.DateField('Invoice date')
    patient_invoice_date = models.DateField('Date envoi au patient', null=True, blank=True)
    invoice_send_date = models.DateField('Date envoi facture', null=True, blank=True)
    invoice_sent = models.BooleanField(default=False)
    invoice_paid = models.BooleanField(default=False)
    batch = models.ForeignKey(InvoiceItemBatch, related_name='invoice_items', null=True, blank=True,
                              on_delete=models.SET_NULL)
    is_valid = models.BooleanField(default=True)
    validation_comment = models.TextField(null=True, blank=True)
    medical_prescription = models.ForeignKey(MedicalPrescription, related_name='invoice_items', null=True, blank=True,
                                             help_text='Please choose a Medical Prescription',
                                             on_delete=models.SET_NULL)

    def clean(self, *args, **kwargs):
        super(InvoiceItem, self).clean_fields()
        messages = self.validate(self.id, self.__dict__)
        if messages:
            raise ValidationError(messages)

    @staticmethod
    def validate(instance_id, data):
        result = {}
        result.update(InvoiceItem.validate_is_private(data))
        result.update(InvoiceItem.validate_patient(data))
        return result

    @staticmethod
    def validate_is_private(data):
        messages = {}
        if data['is_private']:
            patient = None
            if 'patient' in data:
                patient = data['patient']
            elif 'patient_id' in data:
                patient = Patient.objects.filter(pk=data['patient_id']).get()
            else:
                messages = {'patient': 'Please fill Patient field'}

            if patient is not None and data['is_private'] != patient.is_private:
                messages = {'patient': 'Only private Patients allowed in private Invoice Item.'}

        return messages

    @staticmethod
    def validate_patient(data):
        messages = {}
        if 'medical_prescription_id' in data or 'medical_prescription' in data:
            medical_prescription = None
            if 'medical_prescription' in data:
                medical_prescription = data['medical_prescription']
            elif 'medical_prescription_id' in data:
                try:
                    medical_prescription = MedicalPrescription.objects.filter(pk=data['medical_prescription_id']).get()
                except MedicalPrescription.DoesNotExist:
                    medical_prescription = None

            patient = None
            if 'patient' in data:
                patient = data['patient']
            elif 'patient_id' in data:
                patient = Patient.objects.filter(pk=data['patient_id']).get()
            else:
                messages = {'patient': 'Please fill Patient field'}

            if medical_prescription is not None and patient != medical_prescription.patient:
                messages = {
                    'medical_prescription': "MedicalPrescription's Patient must be equal to InvoiceItem's Patient"}

        return messages

    @property
    def invoice_month(self):
        return self.invoice_date.strftime("%B %Y")

    def __str__(self):
        return 'invoice no.: %s - nom patient: %s' % (self.invoice_number, self.patient)

    @staticmethod
    def autocomplete_search_fields():
        return 'invoice_number',


class Prestation(models.Model):
    class Meta:
        ordering = ['-date']
    invoice_item = models.ForeignKey(InvoiceItem,
                                     related_name='prestations',
                                     on_delete=models.CASCADE)
    employee = models.ForeignKey('invoices.Employee',
                                 related_name='prestations',
                                 blank=True,
                                 null=True,
                                 default=settings.AUTH_USER_MODEL,
                                 on_delete=models.CASCADE)
    carecode = models.ForeignKey(CareCode,
                                 related_name='prestations',
                                 on_delete=models.CASCADE)
    quantity = IntegerField(default=1)
    date = models.DateTimeField('date')
    at_home = models.BooleanField(default=False)
    at_home_paired = models.OneToOneField('self',
                                          related_name='paired_at_home',
                                          blank=True,
                                          null=True,
                                          default=None,
                                          on_delete=models.CASCADE)
    date.editable = True

    @property
    def paired_at_home_name(self):
        return str(self.paired_at_home)

    @property
    def at_home_paired_name(self):
        return str(self.at_home_paired)

    def as_dict(self):
        result = self.__dict__
        if self.invoice_item and self.invoice_item.patient is not None:
            result['patient'] = self.invoice_item.patient
            result['invoice_item'] = self.invoice_item

        return result

    def clean(self):
        exclude = []
        if self.invoice_item is not None and self.invoice_item.id is None:
            exclude = ['invoice_item']

        super(Prestation, self).clean_fields(exclude)
        messages = self.validate(self.id, self.as_dict())
        if messages:
            raise ValidationError(messages)

    @staticmethod
    def validate(instance_id, data):
        result = {}
        result.update(Prestation.validate_patient_hospitalization(data))
        result.update(Prestation.validate_at_home_default_config(data))
        result.update(Prestation.validate_carecode(instance_id, data))
        result.update(Prestation.validate_patient_alive(data))
        result.update(Prestation.validate_max_limit(data))
        result.update(Prestation.validate_employee(data))
        return result

    @staticmethod
    def validate_employee(data):
        messages = {}
        employee = None
        if 'employee' in data:
            employee = data['employee']
        elif 'employee_id' in data and data['employee_id'] is not None:
            employee = Employee.objects.filter(pk=data['employee_id']).get()
        else:
            messages = {'employee': 'Please fill Employee field'}
        return messages

    @staticmethod
    def validate_at_home_default_config(data):
        messages = {}
        at_home = 'at_home' in data and data['at_home']
        if at_home and not CareCode.objects.filter(code=config.AT_HOME_CARE_CODE).exists():
            msg = "CareCode %s does not exist. Please create a CareCode with the Code %s" % (
                config.AT_HOME_CARE_CODE, config.AT_HOME_CARE_CODE)
            messages = {'at_home': msg}

        return messages

    @staticmethod
    def validate_patient_hospitalization(data):
        messages = {}
        invoice_item_id = None
        if 'patient' in data:
            patient = data['patient']
        else:
            if 'invoice_item' in data:
                invoice_item_id = data['invoice_item'].id
            elif 'invoice_item_id' in data:
                invoice_item_id = data['invoice_item_id']
            else:
                messages = {'invoice_item_id': 'Please fill InvoiceItem field'}

            patient = Patient.objects.filter(invoice_items__in=[invoice_item_id]).get()

        hospitalizations_cnt = Hospitalization.objects.filter(patient=patient,
                                                              start_date__lte=data['date'],
                                                              end_date__gte=data['date']).count()
        if 0 < hospitalizations_cnt:
            messages = {'date': 'Patient has hospitalization records for the chosen date'}

        return messages

    @staticmethod
    def validate_carecode(instance_id, data):
        messages = {}
        carecode = None
        if 'carecode' in data:
            carecode = data['carecode']
        elif 'carecode_id' in data:
            carecode = CareCode.objects.filter(pk=data['carecode_id']).get()
        else:
            messages = {'carecode_id': 'Please fill CareCode field'}

        invoice_item_id = None
        if 'invoice_item' in data:
            invoice_item_id = data['invoice_item'].id
        elif 'invoice_item_id' in data:
            invoice_item_id = data['invoice_item_id']
        else:
            messages = {'invoice_item_id': 'Please fill InvoiceItem field'}

        exclusive_care_codes = carecode.exclusive_care_codes.all()
        prestations_queryset = Prestation.objects.filter(
            (Q(carecode__in=exclusive_care_codes) | Q(carecode=carecode.id)) & Q(date=data['date']) & Q(
                invoice_item_id=invoice_item_id)).exclude(pk=instance_id)
        prestations_list = prestations_queryset[::1]

        if 0 != len(prestations_list):
            conflicting_codes = ", ".join([prestation.carecode.code for prestation in prestations_list])
            msg = "CareCode %s cannot be applied because CareCode(s) %s has been applied already" % (
                carecode.code, conflicting_codes)

            messages = {'carecode': msg}

        return messages

    @staticmethod
    def validate_patient_alive(data):
        messages = {}
        invoice_item = None
        if 'patient' in data:
            patient = data['patient']
        else:
            if 'invoice_item' in data:
                invoice_item = data['invoice_item']
            elif 'invoice_item_id' in data:
                invoice_item = InvoiceItem.objects.filter(pk=data['invoice_item_id']).get()
            else:
                messages = {'invoice_item_id': 'Please fill InvoiceItem field'}

            patient = invoice_item.patient

        date_of_death = patient.date_of_death
        if date_of_death is not None and data['date'].date() >= date_of_death:
            messages = {'date': "Prestation date cannot be later than or equal to Patient's death date"}

        return messages

    @staticmethod
    def validate_max_limit(data):
        messages = {}
        invoice_item = None
        if 'invoice_item' in data:
            invoice_item = data['invoice_item']
        elif 'invoice_item_id' in data:
            invoice_item = InvoiceItem.objects.filter(pk=data['invoice_item_id']).get()
        else:
            messages = {'invoice_item_id': 'Please fill InvoiceItem field'}

        max_limit = InvoiceItem.PRESTATION_LIMIT_MAX
        existing_prestations = invoice_item.prestations
        existing_count = existing_prestations.count()
        expected_count = existing_count
        adds_new = False
        if 'at_home' in data and data['at_home']:
            at_home_prestation_exists = existing_prestations.filter(carecode__code=config.AT_HOME_CARE_CODE).exists()
            if not at_home_prestation_exists:
                expected_count += 1
                adds_new = True
        if 'id' not in data or data['id'] is None:
            expected_count += 1
            adds_new = True

        if adds_new and expected_count > max_limit:
            messages = {
                'date': "Max number of Prestations for one InvoiceItem is %s" % (str(InvoiceItem.PRESTATION_LIMIT_MAX))}

        return messages

    def __str__(self):  # Python 3: def __str__(self):
        return '%s - %s' % (self.carecode.code, self.carecode.name)

    @staticmethod
    def autocomplete_search_fields():
        return 'patient__name', 'patient__first_name'


@receiver(post_save, sender=Prestation, dispatch_uid="create_at_home_prestation")
def create_prestation_at_home_pair(sender, instance, **kwargs):
    if instance.at_home and instance.at_home_paired is None and not hasattr(instance, 'paired_at_home'):
        at_home_carecode = CareCode.objects.get(code=config.AT_HOME_CARE_CODE)
        at_home_pair_exists = Prestation.objects.filter(invoice_item=instance.invoice_item, date=instance.date,
                                                        carecode=at_home_carecode).exists()
        if not at_home_pair_exists:
            pair = deepcopy(instance)
            pair.pk = None
            pair.carecode = at_home_carecode
            pair.at_home = False
            pair.at_home_paired = instance
            pair.save()


@receiver(post_save, sender=Prestation, dispatch_uid="update_prestation_gcalendar_events")
def update_prestation_gcalendar_events(sender, instance, **kwargs):
    # if config.USE_GDRIVE:
    prestation_gcalendar.update_event(instance)


@receiver(post_delete, sender=Prestation, dispatch_uid="delete_prestation_gcalendar_events")
def delete_prestation_gcalendar_events(sender, instance, **kwargs):
    # if config.USE_GDRIVE:
    prestation_gcalendar.delete_event(instance.id)
