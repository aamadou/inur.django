from django.contrib.auth.models import User, Group
from rest_framework import serializers
from invoices.models import CareCode, Patient, Prestation, InvoiceItem


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'username', 'email')


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ('url', 'name')


class CareCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CareCode
        fields = ('id', 'code', 'name', 'description', 'gross_amount', 'reimbursed')


class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ('id', 'code_sn', 'first_name', 'name', 'address', 'zipcode', 'city', 'phone_number', 'email_address',
                  'participation_statutaire', 'private_patient')


class PrestationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prestation
        fields = ('id', 'patient', 'carecode', 'date')


class InvoiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceItem
        fields = ('id', 'invoice_number', 'accident_id', 'accident_date', 'invoice_date', 'patient_invoice_date',
                  'invoice_send_date', 'invoice_sent', 'invoice_paid', 'medical_prescription_date', 'patient',
                  'prestations')
