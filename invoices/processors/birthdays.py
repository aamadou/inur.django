import re

from django.utils import timezone

from invoices.events import EventType, Event
from invoices.models import Patient, extract_birth_date


def process_and_generate():
    events_processed = []
    even_type_birthday = EventType.objects.filter(to_be_generated=True, name__icontains='Birthdays').first()
    if not even_type_birthday:
        even_type_birthday = EventType(
            name='Birthdays',
            to_be_generated=True
        )
        even_type_birthday.save()

    thisday = timezone.date.today()
    lastday = thisday + timezone.timedelta(days=+30)

    myregexp = re.compile('^[0-9]{4}(' + str(thisday.month).zfill(2) + '|' + str(lastday.month).zfill(2) + ')')

    patients = Patient.objects.filter(code_sn__regex=myregexp.pattern).filter(date_of_death__isnull=True)
    for patient in patients:
        patient_birthday = extract_birth_date(patient.code_sn)
        if patient_birthday.date() > lastday:
            continue
        active_year = thisday.year
        if patient_birthday.month != thisday.month:
            active_year = lastday.year
        searches_date = timezone.date(active_year, patient_birthday.month, patient_birthday.day)
        events = Event.objects.filter(day=searches_date)
        if not events:
            event = Event(
                day=searches_date,
                state=1,
                event_type=even_type_birthday,
                notes='Automatically generated on %d' % timezone.now(),
                patient=patient
            )
            event.save()
            events_processed.append(event)

    return events_processed
