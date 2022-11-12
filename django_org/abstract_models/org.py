from datetime import datetime
from itertools import chain
from typing import List, ForwardRef, Union
from zoneinfo import available_timezones, ZoneInfo

from django.apps import apps
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from django_org.exceptions import NaiveTimeSettingError
from django_org.settings import DJANGO_ORG_ENTERPRISE, DJANGO_ORG_WORK_MODE


__all__ = (
    'AbstractEnterprise',
    'AbstractPost',
)


TIME_ZONES = [(tz, tz) for tz in sorted(list(available_timezones()))]


class AbstractEnterprise(models.Model):
    name = models.CharField(_('Name'), max_length=64, unique=True)
    time_zone = models.CharField(_('Time zone'), max_length=36, choices=TIME_ZONES, default='UTC')

    class Meta:
        abstract = True
        verbose_name = _('Enterprise')
        verbose_name_plural = _('Enterprises')
        ordering = ('name',)

    def __str__(self):
        return self.name

    @property
    def tz(self):
        return ZoneInfo(self.time_zone)

    def get_shifts(self, shift_time: datetime, limit: Union[datetime, int] = 0) -> List[ForwardRef('WorkShift')]:
        WorkMode = apps.get_model(DJANGO_ORG_WORK_MODE)
        if timezone.is_naive(shift_time):
            raise NaiveTimeSettingError('The time must be specified with a time zone')

        shifts = [
            wm.get_shift(shift_time, limit=limit)
            for wm in WorkMode.objects.filter(enterprise=self)
        ]
        if isinstance(limit, int) and -1 <= limit <= 1:
            return shifts

        return list(chain(*shifts))


class AbstractPost(models.Model):
    enterprise = models.ForeignKey(DJANGO_ORG_ENTERPRISE, verbose_name=_('Enterprise'),
                                   related_name='posts', on_delete=models.PROTECT)
    name = models.CharField(_('Name'), max_length=64)

    class Meta:
        abstract = True
        verbose_name = _('Post')
        verbose_name_plural = _('Posts')
        unique_together = ('enterprise', 'name')
        ordering = ('enterprise', 'name')

    def __str__(self):
        return f'{self.enterprise.name}/{self.name}'
