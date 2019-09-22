from datetime import datetime
from django.test import TestCase

from invoices.models import Patient, Physician, InvoiceItem, get_default_invoice_number, MedicalPrescription


class InvoiceItemTestCase(TestCase):
    def setUp(self):
        date = datetime.now()
        self.patient = Patient.objects.create(first_name='first name',
                                              name='name')
        self.private_patient = Patient.objects.create(first_name='first name',
                                                      name='name',
                                                      is_private=True)

        physician = Physician.objects.create(first_name='first name',
                                             name='name')

        self.medical_prescription = MedicalPrescription.objects.create(prescriptor=physician,
                                                                       date=date,
                                                                       patient=self.patient)

        InvoiceItem.objects.create(invoice_number='936 some invoice_number',
                                   invoice_date=date,
                                   patient=self.patient)
        InvoiceItem.objects.create(invoice_number='10',
                                   invoice_date=date,
                                   patient=self.patient)
        InvoiceItem.objects.create(invoice_number='058',
                                   invoice_date=date,
                                   patient=self.patient)
        InvoiceItem.objects.create(invoice_number='147',
                                   invoice_date=date,
                                   patient=self.patient)
        InvoiceItem.objects.create(invoice_number='259',
                                   invoice_date=date,
                                   patient=self.patient)
        InvoiceItem.objects.create(invoice_number='926',
                                   invoice_date=date,
                                   patient=self.patient)

    def test_string_representation(self):
        patient = Patient(first_name='first name',
                          name='name')

        invoice_item = InvoiceItem(patient=patient,
                                   invoice_number='some invoice_number')

        self.assertEqual(str(invoice_item),
                         'invocie no.: %s - nom patient: %s' % (invoice_item.invoice_number, invoice_item.patient))

    def test_autocomplete(self):
        self.assertEqual(InvoiceItem.autocomplete_search_fields(), ('invoice_number',))

    def test_invoice_month(self):
        date = datetime.now()
        invoice_item = InvoiceItem(invoice_date=date)

        self.assertEqual(invoice_item.invoice_month, date.strftime("%B %Y"))

    def test_default_invoice_number(self):
        self.assertEqual(get_default_invoice_number(), 927)

    def test_validate_is_private(self):
        error_message = {'patient': 'Only private Patients allowed in private Invoice Item.'}
        data = {
            'patient_id': self.patient.id,
            'is_private': False
        }

        self.assertEqual(InvoiceItem.validate_is_private(data), {})

        data['is_private'] = True
        self.assertEqual(InvoiceItem.validate_is_private(data), error_message)

        data['patient_id'] = self.private_patient.id
        self.assertEqual(InvoiceItem.validate_is_private(data), {})

        data['is_private'] = False
        self.assertEqual(InvoiceItem.validate_is_private(data), {})

    def test_validate_patient(self):
        error_message = {'medical_prescription': "MedicalPrescription's Patient must be equal to InvoiceItem's Patient"}

        data = {
            'patient_id': self.patient.id
        }

        self.assertEqual(InvoiceItem.validate_patient(data), {})

        data['medical_prescription_id'] = self.medical_prescription.id
        self.assertEqual(InvoiceItem.validate_patient(data), {})

        data['patient_id'] = self.private_patient.id
        self.assertEqual(InvoiceItem.validate_patient(data), error_message)