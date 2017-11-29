from datetime import datetime
from django.test import TestCase

from invoices.models import CareCode, Patient, Physician, Prestation, InvoiceItem, get_default_invoice_number


class CareCodeTestCase(TestCase):
    def test_string_representation(self):
        carecode = CareCode(code='code',
                            name='some name',
                            description='description',
                            gross_amount=10.2,
                            reimbursed=False)

        self.assertEqual(str(carecode), '%s: %s' % (carecode.code, carecode.name))

    def test_autocomplete(self):
        self.assertEqual(CareCode.autocomplete_search_fields(), ('name', 'code'))


class PatientTestCase(TestCase):
    def test_string_representation(self):
        patient = Patient(first_name='first name',
                          name='name')

        self.assertEqual(str(patient), '%s %s' % (patient.name.strip(), patient.first_name.strip()))

    def test_autocomplete(self):
        self.assertEqual(Patient.autocomplete_search_fields(), ('name', 'first_name'))


class PhysicianTestCase(TestCase):
    def test_string_representation(self):
        physician = Physician(first_name='first name',
                              name='name')

        self.assertEqual(str(physician), '%s %s' % (physician.name.strip(), physician.first_name.strip()))

    def test_autocomplete(self):
        self.assertEqual(Physician.autocomplete_search_fields(), ('name', 'first_name'))


class PrestationTestCase(TestCase):
    def test_string_representation(self):
        carecode = CareCode(code='code',
                            name='some name',
                            description='description',
                            gross_amount=10.2,
                            reimbursed=False)

        prestation = Prestation(carecode=carecode)

        self.assertEqual(str(prestation), '%s - %s' % (prestation.carecode.code, prestation.carecode.name))

    def test_autocomplete(self):
        self.assertEqual(Prestation.autocomplete_search_fields(), ('patient__name', 'patient__first_name'))


class InvoiceItemTestCase(TestCase):
    def setUp(self):
        patient = Patient.objects.create(first_name='first name',
                                         name='name')

        date = datetime.now()
        InvoiceItem.objects.create(invoice_number='936 some invoice_number',
                                   invoice_date=date,
                                   patient=patient)
        InvoiceItem.objects.create(invoice_number='10',
                                   invoice_date=date,
                                   patient=patient)
        InvoiceItem.objects.create(invoice_number='058',
                                   invoice_date=date,
                                   patient=patient)
        InvoiceItem.objects.create(invoice_number='147',
                                   invoice_date=date,
                                   patient=patient)
        InvoiceItem.objects.create(invoice_number='259',
                                   invoice_date=date,
                                   patient=patient)
        InvoiceItem.objects.create(invoice_number='926',
                                   invoice_date=date,
                                   patient=patient)

    def test_string_representation(self):
        patient = Patient(first_name='first name',
                          name='name')

        invoice_item = InvoiceItem(patient=patient,
                                   invoice_number='some invoice_number')

        self.assertEqual(str(invoice_item),
                         'invocie no.: %s - nom patient: %s' % (invoice_item.invoice_number, invoice_item.patient))

    def test_autocomplete(self):
        self.assertEqual(InvoiceItem.autocomplete_search_fields(), 'invoice_number')

    def test_invoice_month(self):
        date = datetime.now()
        invoice_item = InvoiceItem(invoice_date=date)

        self.assertEqual(invoice_item.invoice_month, date.strftime("%B %Y"))

    def test_default_invoice_number(self):
        self.assertEqual(get_default_invoice_number(), 927)