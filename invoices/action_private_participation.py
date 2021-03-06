# -*- coding: utf-8 -*-
import decimal

from constance import config
from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus.doctemplate import SimpleDocTemplate
from reportlab.platypus.flowables import Spacer, PageBreak
from reportlab.platypus.para import Paragraph
from reportlab.platypus.tables import Table, TableStyle
from django.utils.timezone import now
from django.utils.encoding import smart_text
from django.utils.translation import gettext_lazy as _

def pdf_private_invoice_pp(modeladmin, request, queryset):
    # Create the HttpResponse object with the appropriate PDF headers.
    response = HttpResponse(content_type='application/pdf')
    # Append invoice number and invoice date
    if len(queryset) != 1:
        _file_name = '-'.join([a.invoice_number for a in queryset.order_by("invoice_number")])
        _payment_ref = _file_name.replace(" ", "")[:10]
        _recap_date = now().date().strftime('%d-%m-%Y')
        response['Content-Disposition'] = 'attachment; filename="invoice%s.pdf"' % (_file_name.replace(" ", "")[:150])
    else:
        _payment_ref = "PI.%s %s" % (queryset[0].invoice_number, queryset[0].invoice_date.strftime('%d.%m.%Y'))
        _recap_date = queryset[0].invoice_date.strftime('%d-%m-%Y')
        response['Content-Disposition'] = 'attachment; filename="invoice-%s-%s-%s-part-personnelle.pdf"' % (
        queryset[0].patient.name,
        queryset[0].invoice_number,
        queryset[0].invoice_date.strftime('%d-%m-%Y'))

    elements = []
    doc = SimpleDocTemplate(response, rightMargin=2 * cm, leftMargin=2 * cm, topMargin=1 * cm, bottomMargin=1 * cm)

    recapitulatif_data = []

    for qs in queryset.order_by("invoice_number"):
        dd = [qs.prestations.all().order_by("date", "carecode__name")[i:i + 20] for i in
              range(0, len(qs.prestations.all()), 20)]
        for _prestations in dd:
            _inv = qs.invoice_number + (
            ("" + str(dd.index(_prestations) + 1) + qs.invoice_date.strftime('%m%Y')) if len(dd) > 1 else "")
            _result = _build_invoices(_prestations,
                                      _inv,
                                      qs.invoice_date,
                                      qs.medical_prescription,
                                      qs.accident_id,
                                      qs.accident_date,
                                      qs.patient_invoice_date,
                                      qs.patient)

            elements.extend(_result["elements"])
            recapitulatif_data.append((_result["invoice_number"], _result["patient_name"], _result["invoice_pp"]))
            elements.append(PageBreak())

    elements.extend(_build_recap(_recap_date, _payment_ref, recapitulatif_data))
    doc.build(elements)
    return response


def _build_invoices(prestations, invoice_number, invoice_date, prescription_date, accident_id, accident_date,
                    patient_invoice_date, patient):
    # Draw things on the PDF. Here's where the PDF generation happens.
    # See the ReportLab documentation for the full list of functionality.
    elements = []
    i = 0
    data = []
    patientSocNumber = ''
    patientNameAndFirstName = ''
    patientName = '';
    patient_first_name = '';
    patient_address = ''

    data.append(('Num. titre', 'Prestation', 'Date', 'Nombre', 'Brut', 'CNS', 'Part. Client'))
    for presta in prestations:
        i += 1
        patientSocNumber = patient.code_sn
        patientNameAndFirstName = patient
        patientName = patient.name
        patient_first_name = patient.first_name
        patient_address = patient.address
        patientZipCode = patient.zipcode
        patientCity = patient.city
        data.append((i, presta.carecode.code,
                     (presta.date).strftime('%d/%m/%Y'),
                     '1',
                     presta.carecode.gross_amount(presta.date),
                     presta.carecode.net_amount(presta.date,
                                                patient.is_private,
                                                patient.participation_statutaire
                                                and patient.age > 18),
                     "%10.2f" % (decimal.Decimal(presta.carecode.gross_amount(presta.date)) -
                                                 decimal.Decimal(presta.carecode.net_amount(presta.date,
                                                                                            patient.is_private,
                                                                                            patient.participation_statutaire)))))

    for x in range(len(data), 22):
        data.append((x, '', '', '', '', '', ''))

    newData = []
    for y in range(0, len(data) - 1):
        newData.append(data[y])
        if (y % 10 == 0 and y != 0):
            _gross_sum = _compute_sum(data[y - 9:y + 1], 4)
            _net_sum = _compute_sum(data[y - 9:y + 1], 5)
            _part_sum = _compute_sum(data[y - 9:y + 1], 6)
            newData.append(('', '', '', 'Sous-Total', "%10.2f" % _gross_sum, "%10.2f" % _net_sum, "%10.2f" % _part_sum))
    _total_facture = _compute_sum(data[1:], 5)
    _participation_personnelle = decimal.Decimal(_compute_sum(data[1:], 4)) - decimal.Decimal(_total_facture)
    newData.append(('', '', '', 'Total', "%10.2f" % _compute_sum(data[1:], 4), "%10.2f" % _compute_sum(data[1:], 5),
                    "%10.2f" % _compute_sum(data[1:], 6)))

    headerData = [['IDENTIFICATION DU FOURNISSEUR DE SOINS DE SANTE\n'
                   + "{0}\n{1}\n{2}\n{3}".format(config.NURSE_NAME,
                                                 config.NURSE_ADDRESS,
                                                 config.NURSE_ZIP_CODE_CITY,
                                                 config.NURSE_PHONE_NUMBER),
                   'CODE DU FOURNISSEUR DE SOINS DE SANTE\n{0}'.format(config.MAIN_NURSE_CODE)
                   ],
                  [u'Matricule patient: %s' % smart_text(patientSocNumber.strip()) + "\n"
                   + u'Nom et Pr' + smart_text("e") + u'nom du patient: %s' % smart_text(patientNameAndFirstName),
                   u'Nom: %s' % smart_text(patientName.strip()) + '\n'
                   + u'Pr' + smart_text(u"é") + u'nom: %s' % smart_text(patient_first_name.strip()) + '\n'
                   + u'Rue: %s' % patient_address.strip() + '\n'
                   + u'Code postal: %s' % smart_text(patientZipCode.strip()) + '\n'
                   + u'Ville: %s' % smart_text(patientCity.strip())],
                  [u'Date accident: %s\n' % (accident_date if accident_date else "")
                   + u'Num. accident: %s' % (accident_id if accident_id else "")]]

    headerTable = Table(headerData, 2 * [10 * cm], [2.5 * cm, 1 * cm, 1.5 * cm])
    headerTable.setStyle(TableStyle([('ALIGN', (1, 1), (-2, -2), 'LEFT'),
                                     ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                                     ('FONTSIZE', (0, 0), (-1, -1), 9),
                                     ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
                                     ('SPAN', (1, 1), (1, 2)),
                                     ]))

    table = Table(newData, 9 * [2.5 * cm], 24 * [0.5 * cm])
    table.setStyle(TableStyle([('ALIGN', (1, 1), (-2, -2), 'LEFT'),
                               ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                               ('ALIGN', (0, -1), (-6, -1), 'RIGHT'),
                               ('INNERGRID', (0, -1), (-6, -1), 0, colors.white),
                               ('ALIGN', (0, -2), (-6, -2), 'RIGHT'),
                               ('INNERGRID', (0, -2), (-6, -2), 0, colors.white),
                               ('FONTSIZE', (0, 0), (-1, -1), 8),
                               ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
                               ]))

    elements.append(headerTable)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER))
    elements.append(Spacer(1, 18))
    if (prescription_date is not None):
        elements.append(Paragraph(u"Mémoire d'Honoraires Num. %s en date du : %s Ordonnance du %s " % (
        invoice_number, invoice_date, prescription_date), styles['Heading4']))
    else:
        elements.append(Paragraph(u"Mémoire d'Honoraires Num. %s en date du : %s " % (invoice_number, invoice_date),
                                  styles['Heading4']))

    elements.append(Spacer(1, 18))

    elements.append(table)

    elements.append(Spacer(1, 18))

    _total_a_payer = Table([["Total participation personnelle:", "%10.2f Euros" % _participation_personnelle]],
                           [10 * cm, 5 * cm], 1 * [0.5 * cm], hAlign='LEFT')
    elements.append(Spacer(1, 18))
    elements.append(_total_a_payer)
    elements.append(Spacer(1, 18))

    elements.append(Spacer(1, 10))

    if patient_invoice_date is not None:
        from utils import setlocale
        with setlocale('en_GB.utf8'):
            if isinstance(patient_invoice_date, unicode):
                elements.append(Table([[u"Date envoi de la présente facture: %s " % patient_invoice_date.strftime(
                    '%d %B %Y').encode('utf-8')]], [10 * cm], 1 * [0.5 * cm], hAlign='LEFT'))
            else:
                elements.append(Table([[u"Date envoi de la présente facture: %s " % patient_invoice_date.strftime(
                    '%d %B %Y').decode('utf-8')]], [10 * cm], 1 * [0.5 * cm], hAlign='LEFT'))
        elements.append(Spacer(1, 10))

    return {"elements": elements
        , "invoice_number": invoice_number
        , "patient_name": patientName + " " + patient_first_name
        , "invoice_amount": newData[23][5]
        , "invoice_pp": newData[23][6]}


pdf_private_invoice_pp.short_description = _("Personal participation")


def _compute_sum(data, position):
    sum = 0
    for x in data:
        if x[position] != "":
            sum += decimal.Decimal(x[position])
    return sum


def _build_recap(_recap_date, _recap_ref, recaps):
    """
    """
    elements = []

    _intro = Table([[
                        u"Veuillez trouver ci-joint le récapitulatif des factures ainsi que le montant total à payer"]],
                   [10 * cm, 5 * cm], 1 * [0.5 * cm], hAlign='LEFT')
    elements.append(_intro)
    elements.append(Spacer(1, 18))

    data = []
    i = 0
    data.append(("N d'ordre", u"Note no°", u"Nom et prénom", "Montant"))
    total = 0.0
    _invoice_nrs = "";
    for recap in recaps:
        i += 1
        data.append((i, recap[0], recap[1], recap[2]))
        total = decimal.Decimal(total) + decimal.Decimal(recap[2])
        _invoice_nrs += "-" + recap[0]
    data.append(("", "", u"à reporter", round(total, 2), ""))

    table = Table(data, [2 * cm, 3 * cm, 7 * cm, 3 * cm], (i + 2) * [0.75 * cm])
    table.setStyle(TableStyle([('ALIGN', (1, 1), (-2, -2), 'LEFT'),
                               ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                               ('FONTSIZE', (0, 0), (-1, -1), 9),
                               ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
                               ]))
    elements.append(table)

    elements.append(Spacer(1, 18))

    elements.append(Spacer(1, 18))
    _infos_iban = Table([["Lors du virement, veuillez indiquer la r" + u"é" + "f" + u"é" + "rence: %s " % _recap_ref]],
                        [10 * cm], 1 * [0.5 * cm], hAlign='LEFT')
    _date_infos = Table([["Date facture : %s " % _recap_date]], [10 * cm], 1 * [0.5 * cm], hAlign='LEFT')

    elements.append(_date_infos)
    elements.append(Spacer(1, 18))
    elements.append(_infos_iban)
    elements.append(Spacer(1, 18))
    _total_a_payer = Table([["Total " + u"à" + " payer:", "%10.2f Euros" % total]], [10 * cm, 5 * cm], 1 * [0.5 * cm],
                           hAlign='LEFT')
    elements.append(_total_a_payer)
    elements.append(Spacer(1, 18))

    _infos_iban = Table([[u"Numéro IBAN: %s" % config.MAIN_BANK_ACCOUNT]], [10*cm], 1*[0.5*cm], hAlign='LEFT')
    elements.append(_infos_iban)

    return elements
