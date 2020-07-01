# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.urls import reverse
from invoices.models import Patient
from django.utils.translation import gettext as _


class EventType(models.Model):
    class Meta:
        verbose_name = _('Event -> Type')
        verbose_name_plural = _('Event -> Types')
        ordering = ['-id']

    name = models.CharField(_('Descriptive Name'), max_length=50)
    to_be_generated = models.BooleanField(_('To be generated'),
                                          help_text=_('If checked, these type of events types will be generated auto.'),
                                          default=False)

    @staticmethod
    def autocomplete_search_fields():
        return 'name'

    def __str__(self):  # Python 3: def __str__(self):,
        return '%s' % (self.name.strip())


class Event(models.Model):
    class Meta:
        verbose_name = _('Event')
        verbose_name_plural = _('Events')

    STATES = [
        (1, _('Waiting for validation')),
        (2, _('Valid')),
        (3, _('Done')),
        (4, _('Ignored'))
    ]

    day = models.DateField(_('Event day'), help_text=_('Event day'))
    state = models.PositiveSmallIntegerField(choices=STATES)
    event_type = models.ForeignKey(EventType, blank=True, null=True,
                                   help_text=_('Event type'),
                                   on_delete=models.SET_NULL)
    notes = models.TextField(
        _('Notes'),
        help_text=_('Notes'), blank=True, null=True)
    patient = models.ForeignKey(Patient, related_name='event_link_to_patient', blank=True, null=True,
                                help_text=_('Please select a patient'),
                                on_delete=models.CASCADE)

    def get_absolute_url(self):
        url = reverse('admin:%s_%s_change' % (self._meta.app_label, self._meta.model_name), args=[self.id])
        return u'<a href="%s">%s</a>' % (url, str(self.day))

    def __str__(self):  # Python 3: def __str__(self):,
        return '%s for %s on %s' % (self.event_type, self.patient, self.day)