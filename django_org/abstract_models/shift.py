from datetime import date, datetime, timedelta
from enum import Enum
from itertools import chain
from operator import attrgetter
from typing import List, ForwardRef, Optional, Tuple, Union

from django.apps import apps
from django.db import models
from django.db.models import F, Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from django_org.exceptions import NaiveTimeSettingError
from django_org.const import SEC1, SECONDS_IN_DAY
from django_org.settings import DJANGO_ORG_ENTERPRISE, DJANGO_ORG_WORK_MODE, DJANGO_ORG_WORK_SHIFT
from django_org.utils import _day_start, _datetime


__all__ = (
    'AbstractWorkMode',
    'AbstractWorkShift',
)


class Direction(Enum):
    NEXT = True
    PREV = False


class AbstractWorkMode(models.Model):
    enterprise = models.ForeignKey(DJANGO_ORG_ENTERPRISE, verbose_name=_('Enterprise'), on_delete=models.PROTECT)
    name = models.CharField(_('Name'), max_length=36)

    class Meta:
        abstract = True
        verbose_name = _('Work mode')
        verbose_name_plural = _('Work modes')
        unique_together = ('enterprise', 'name')
        ordering = ('enterprise', 'name')

    def __str__(self):
        return f'{self.enterprise.name}/{self.name}'

    def get_shift(
            self,
            shift_time: datetime,
            limit: Union[datetime, int] = 0
    ) -> Optional[Union[ForwardRef('WorkShift'), List[ForwardRef('WorkShift')]]]:
        WorkShift = apps.get_model(DJANGO_ORG_WORK_SHIFT)
        if timezone.is_naive(shift_time):
            raise NaiveTimeSettingError('The time must be specified with a time zone')

        st = shift_time.astimezone(tz=self.enterprise.tz)
        seconds = int((st - _day_start(st)).total_seconds())
        q = (
                (Q(start__gt=F('end')) & Q(start__lte=seconds) & Q(end__lt=seconds))
                | (Q(start__lt=F('end')) & Q(start__lte=seconds) & Q(end__gt=seconds))
                | (Q(start__gt=F('end')) & Q(start__gt=seconds) & Q(end__gt=seconds))
        )
        shift = WorkShift.objects.filter(q, work_mode=self).order_by('number').first()
        shift.work_shift(st)

        if isinstance(limit, int):
            if -1 <= limit <= 1: return shift
            backward = limit < 0
        else:
            backward = limit < shift_time

        shift_set = list(self.shift_set.order_by('number'))

        if backward:
            shift_set.reverse()
            sec1 = -SEC1
            shift_edge = attrgetter('start_time')
        else:
            sec1 = SEC1
            shift_edge = attrgetter('end_time')

        shift_fields = [field.name for field in shift._meta.fields]
        _fields = attrgetter(*shift_fields)
        shifts = [shift]
        shift_count = len(shift_set)
        i = shift_set.index(shift) + 1
        if i >= shift_count: i = 0

        if isinstance(limit, int):
            count = 1
            while count < abs(limit):
                s = WorkShift(**dict(zip(shift_fields, _fields(shift_set[i]))))
                shifts.append(s.work_shift(shift_edge(shifts[-1]) + sec1))
                i += 1
                if i >= shift_count: i = 0
                count += 1
        else:
            while not shifts[-1].start_time <= limit < shifts[-1].end_time:
                s = WorkShift(**dict(zip(shift_fields, _fields(shift_set[i]))))
                shifts.append(s.work_shift(shift_edge(shifts[-1]) + sec1))
                i += 1
                if i >= shift_count: i = 0

        return shifts

    @classmethod
    def get_shifts(cls, shift_time: datetime, limit: Union[datetime, int] = 0) -> List[ForwardRef('WorkShift')]:
        if timezone.is_naive(shift_time):
            raise NaiveTimeSettingError('The time must be specified with a time zone')

        shifts = [wm.get_shift(shift_time, limit=limit) for wm in cls.objects.all()]
        if isinstance(limit, int) and -1 <= limit <= 1:
            return shifts

        return list(chain(*shifts))


class AbstractWorkShift(models.Model):
    enterprise = models.ForeignKey(DJANGO_ORG_ENTERPRISE, verbose_name=_('Enterprise'),
                                   on_delete=models.PROTECT, editable=False)
    work_mode = models.ForeignKey(DJANGO_ORG_WORK_MODE, verbose_name=_('Work mode'),
                                  related_name='shift_set', on_delete=models.PROTECT)
    name = models.CharField(_('Name'), max_length=36)
    number = models.PositiveSmallIntegerField(_('Shift number'))
    start = models.PositiveIntegerField(_('Shift start indent, sec.'), default=0)
    end = models.PositiveIntegerField(_('Shift end indent, sec.'), default=43200)

    class Meta:
        abstract = True
        verbose_name = _('Work shift')
        verbose_name_plural = _('Work shifts')
        unique_together = (('work_mode', 'name'), ('work_mode', 'number'))
        ordering = ('enterprise__name', 'work_mode__name', 'number')

    def __str__(self):
        return f'{self.enterprise.name}/{self.work_mode.name}/{self.name}'

    def save(self, **kwargs):
        if self.enterprise_id is None:
            self.enterprise_id = self.work_mode.enterprise_id

        super().save(**kwargs)

    def borders(self, shift_time: datetime) -> Tuple[datetime, datetime]:
        day_start = _day_start(shift_time).replace(tzinfo=self.enterprise.tz)
        if self.start < self.end:
            start = day_start + timedelta(seconds=self.start)
            end = day_start + timedelta(seconds=self.end)
        elif self.number > 1:
            start = day_start + timedelta(seconds=self.start)
            end = day_start + timedelta(seconds=self.end) + SECONDS_IN_DAY
        else:
            start = day_start + timedelta(seconds=self.start) - SECONDS_IN_DAY
            end = day_start + timedelta(seconds=self.end)

        if not start <= shift_time < end:
            if (start + SECONDS_IN_DAY <= shift_time < end + SECONDS_IN_DAY):
                start += SECONDS_IN_DAY
                end += SECONDS_IN_DAY
            elif (start - SECONDS_IN_DAY <= shift_time < end - SECONDS_IN_DAY):
                start -= SECONDS_IN_DAY
                end -= SECONDS_IN_DAY

        return start, end

    @staticmethod
    def make_work_shift(
            shift: Optional[ForwardRef('WorkShift')],
            shift_time: datetime,
            now: Optional[datetime] = None
    ) -> Optional[ForwardRef('WorkShift')]:
        if shift is None:
            return None
        if timezone.is_naive(shift_time):
            raise NaiveTimeSettingError('The time must be specified with a time zone')
        if now and timezone.is_naive(now):
            raise NaiveTimeSettingError('The time must be specified with a time zone')

        shift.shift_time = shift_time
        shift.now = now or timezone.now()
        shift.start_time, shift.end_time = shift.borders(shift.shift_time)
        start_day_time = _day_start(shift.shift_time)
        end_day_time = start_day_time + SECONDS_IN_DAY
        if (
                shift.number == 1
                and (
                    shift.start_time.day < shift.end_time.day
                    or shift.start_time.month < shift.end_time.month
                    or shift.start_time.year < shift.end_time.year
                )
                and shift.start_time.day == shift.shift_time.day
        ):
            shift.shift_day_time = end_day_time
        else:
            shift.shift_day_time = start_day_time
        shift.shift_day = shift.shift_day_time.date()
        shift.is_current = shift.start_time <= shift.now < shift.end_time
        return shift

    def work_shift(self, shift_time: Union[date, datetime]) -> Optional[ForwardRef('WorkShift')]:
        if not isinstance(shift_time, datetime):
            shift_time = _datetime(shift_time, tzinfo=self.enterprise.tz)
        return self.__class__.make_work_shift(self, shift_time)

    def _step(self, direction: Direction) -> ForwardRef('WorkShift'):
        if not getattr(self, 'shift_time', None):
            return self.work_shift(timezone.now())._step(direction)

        if not getattr(self, '_work_shifts', []):
            fields = [f.name for f in self._meta.fields if f.name not in ('id', 'work_mode', 'enterprise')]
            fields.insert(0, 'id')
            fields.insert(1, 'enterprise_id')
            fields.insert(2, 'work_mode_id')
            f = lambda v: tuple(zip(fields, v))
            self._work_shifts = list(map(f, self.work_mode.shift_set.order_by('number').values_list(*fields)))

        shift_set = self._work_shifts.copy()
        if direction is Direction.PREV:
            shift_set.reverse()
            shift_time = getattr(self, 'start_time') - SEC1
        else:
            shift_time = getattr(self, 'end_time') + SEC1

        shifts = [s[0][1] for s in shift_set]
        i = shifts.index(self.id) + 1
        if i >= len(shifts): i = 0

        shift = self.__class__(**dict(shift_set[i])).work_shift(shift_time)
        shift._work_shifts = self._work_shifts.copy()
        return shift

    def next(self) -> ForwardRef('WorkShift'):
        return self._step(Direction.NEXT)

    def prev(self) -> ForwardRef('WorkShift'):
        return self._step(Direction.PREV)
