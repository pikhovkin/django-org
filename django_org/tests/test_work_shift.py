import datetime

from django.db import transaction
from django.db.utils import IntegrityError
from django.test import TestCase
from django.utils import timezone

from django_org import models
from django_org.const import SEC1, HOUR1, SECONDS_IN_DAY
from django_org.utils import _day_start


class WorkShiftTest(TestCase):
    N01 = HOUR1.total_seconds()
    N08 = 8 * N01
    N20 = 20 * N01
    H08 = datetime.timedelta(seconds=N08)
    H20 = datetime.timedelta(seconds=N20)

    def setUp(self):
        self.enterprise1 = models.Enterprise.objects.create(name='Enterprise1')
        self.wm2 = models.WorkMode.objects.create(enterprise=self.enterprise1, name='WorkMode2')

        self.curr_day = _day_start(timezone.now().astimezone(self.enterprise1.tz))
        self.prev_day = self.curr_day - SECONDS_IN_DAY
        self.next_day = self.curr_day + SECONDS_IN_DAY

    def test_simple_creation(self):
        models.WorkShift.objects.create(work_mode=self.wm2, name='TestWorkShift1', number=1)
        models.WorkShift.objects.create(work_mode=self.wm2, name='TestWorkShift2', number=2)
        with self.assertRaises(IntegrityError), transaction.atomic():
            models.WorkShift.objects.create(work_mode=self.wm2, name='TestWorkShift1', number=3)
        with self.assertRaises(IntegrityError), transaction.atomic():
            models.WorkShift.objects.create(work_mode=self.wm2, name='TestWorkShift2', number=1)

    def test_prev_curr_shifts_borders(self):
        shift21 = models.WorkShift.objects.create(
            work_mode=self.wm2, name='TestWorkShift1', number=1, start=self.N20, end=self.N08)
        shift22 = models.WorkShift.objects.create(
            work_mode=self.wm2, name='TestWorkShift2', number=2, start=self.N08, end=self.N20)

        start = self.prev_day + self.H20 - SECONDS_IN_DAY
        end = self.prev_day + self.H08
        self.assertTrue(shift21.borders(self.prev_day) == (start, end))
        start = self.prev_day + self.H08
        end = self.prev_day + self.H20
        self.assertTrue(shift22.borders(self.prev_day) == (start, end))

        start = self.prev_day + self.H20
        end = self.curr_day + self.H08
        self.assertTrue(shift21.borders(self.curr_day) == (start, end))
        start = self.curr_day + self.H08
        end = self.curr_day + self.H20
        self.assertTrue(shift22.borders(self.curr_day) == (start, end))

        start = self.curr_day + self.H20
        end = self.next_day + self.H08
        self.assertTrue(shift21.borders(self.next_day) == (start, end))
        start = self.next_day + self.H08
        end = self.next_day + self.H20
        self.assertTrue(shift22.borders(self.next_day) == (start, end))

    def test_curr_next_shifts_borders(self):
        shift21 = models.WorkShift.objects.create(
            work_mode=self.wm2, name='TestWorkShift1', number=1, start=self.N08, end=self.N20)
        shift22 = models.WorkShift.objects.create(
            work_mode=self.wm2, name='TestWorkShift2', number=2, start=self.N20, end=self.N08)

        start = self.prev_day + self.H08
        end = self.prev_day + self.H20
        self.assertTrue(shift21.borders(self.prev_day) == (start, end))
        start = self.prev_day + self.H20 - SECONDS_IN_DAY
        end = self.prev_day + self.H08
        self.assertTrue(shift22.borders(self.prev_day) == (start, end))

        start = self.curr_day + self.H08
        end = self.curr_day + self.H20
        self.assertTrue(shift21.borders(self.curr_day) == (start, end))
        start = self.prev_day + self.H20
        end = self.curr_day + self.H08
        self.assertTrue(shift22.borders(self.curr_day) == (start, end))

        start = self.next_day + self.H08
        end = self.next_day + self.H20
        self.assertTrue(shift21.borders(self.next_day) == (start, end))
        start = self.curr_day + self.H20
        end = self.next_day + self.H08
        self.assertTrue(shift22.borders(self.next_day) == (start, end))

    def test_simple_next(self):
        shift21 = models.WorkShift.objects.create(
            work_mode=self.wm2, name='TestWorkShift1', number=1, start=self.N08, end=self.N20)
        shift22 = models.WorkShift.objects.create(
            work_mode=self.wm2, name='TestWorkShift2', number=2, start=self.N20, end=self.N08)

        shift = shift22.work_shift(self.prev_day + self.H08 - SEC1)

        shift = shift.next()
        start = self.prev_day + self.H08
        end = self.prev_day + self.H20
        self.assertTrue((shift.start_time, shift.end_time) == (start, end))
        self.assertTrue(shift.id == shift.pk)
        self.assertTrue(shift.id == shift21.id)
        self.assertTrue(shift.name == shift21.name)
        self.assertTrue(shift.work_mode == shift21.work_mode)

        shift = shift.next()
        start = self.prev_day + self.H20
        end = self.curr_day + self.H08
        self.assertTrue((shift.start_time, shift.end_time) == (start, end))
        self.assertTrue(shift.id == shift.pk)
        self.assertTrue(shift.id == shift22.id)
        self.assertTrue(shift.name == shift22.name)
        self.assertTrue(shift.work_mode == shift22.work_mode)

        shift = shift.next()
        start = self.curr_day + self.H08
        end = self.curr_day + self.H20
        self.assertTrue((shift.start_time, shift.end_time) == (start, end))
        self.assertTrue(shift.id == shift.pk)
        self.assertTrue(shift.id == shift21.id)
        self.assertTrue(shift.name == shift21.name)
        self.assertTrue(shift.work_mode == shift21.work_mode)

        shift = shift.next()
        start = self.curr_day + self.H20
        end = self.next_day + self.H08
        self.assertTrue((shift.start_time, shift.end_time) == (start, end))
        self.assertTrue(shift.id == shift.pk)
        self.assertTrue(shift.id == shift22.id)
        self.assertTrue(shift.name == shift22.name)
        self.assertTrue(shift.work_mode == shift22.work_mode)

        shift = shift.next()
        start = self.next_day + self.H08
        end = self.next_day + self.H20
        self.assertTrue((shift.start_time, shift.end_time) == (start, end))
        self.assertTrue(shift.id == shift.pk)
        self.assertTrue(shift.id == shift21.id)
        self.assertTrue(shift.name == shift21.name)
        self.assertTrue(shift.work_mode == shift21.work_mode)

    def test_next(self):
        shift21 = models.WorkShift.objects.create(
            work_mode=self.wm2, name='TestWorkShift1', number=1, start=self.N08, end=self.N20)
        shift22 = models.WorkShift.objects.create(
            work_mode=self.wm2, name='TestWorkShift2', number=2, start=self.N20, end=self.N08)

        shift = shift22.work_shift(self.prev_day + self.H08 - SEC1)

        n = 0
        while n < 5:
            shift = shift.next()
            n += 1

        start = self.next_day + self.H08
        end = self.next_day + self.H20
        self.assertTrue((shift.start_time, shift.end_time) == (start, end))
        self.assertTrue(shift.id == shift.pk)
        self.assertTrue(shift.id == shift21.id)
        self.assertTrue(shift.name == shift21.name)
        self.assertTrue(shift.work_mode == shift21.work_mode)

        shift = shift22.work_shift(self.prev_day + self.H08 - SEC1)

        while shift.start_time < self.next_day + self.H08:
            shift = shift.next()

        start = self.next_day + self.H08
        end = self.next_day + self.H20
        self.assertTrue((shift.start_time, shift.end_time) == (start, end))
        self.assertTrue(shift.id == shift.pk)
        self.assertTrue(shift.id == shift21.id)
        self.assertTrue(shift.name == shift21.name)
        self.assertTrue(shift.work_mode == shift21.work_mode)

    def test_simple_prev(self):
        shift21 = models.WorkShift.objects.create(
            work_mode=self.wm2, name='TestWorkShift1', number=1, start=self.N20, end=self.N08)
        shift22 = models.WorkShift.objects.create(
            work_mode=self.wm2, name='TestWorkShift2', number=2, start=self.N08, end=self.N20)

        shift = shift21.work_shift(self.next_day + self.H20)

        shift = shift.prev()
        start = self.next_day + self.H08
        end = self.next_day + self.H20
        self.assertTrue((shift.start_time, shift.end_time) == (start, end))
        self.assertTrue(shift.id == shift.pk)
        self.assertTrue(shift.id == shift22.id)
        self.assertTrue(shift.name == shift22.name)
        self.assertTrue(shift.work_mode == shift22.work_mode)

        shift = shift.prev()
        start = self.curr_day + self.H20
        end = self.next_day + self.H08
        self.assertTrue((shift.start_time, shift.end_time) == (start, end))
        self.assertTrue(shift.id == shift.pk)
        self.assertTrue(shift.id == shift21.id)
        self.assertTrue(shift.name == shift21.name)
        self.assertTrue(shift.work_mode == shift21.work_mode)

        shift = shift.prev()
        start = self.curr_day + self.H08
        end = self.curr_day + self.H20
        self.assertTrue((shift.start_time, shift.end_time) == (start, end))
        self.assertTrue(shift.id == shift.pk)
        self.assertTrue(shift.id == shift22.id)
        self.assertTrue(shift.name == shift22.name)
        self.assertTrue(shift.work_mode == shift22.work_mode)

        shift = shift.prev()
        start = self.prev_day + self.H20
        end = self.curr_day + self.H08
        self.assertTrue((shift.start_time, shift.end_time) == (start, end))
        self.assertTrue(shift.id == shift.pk)
        self.assertTrue(shift.id == shift21.id)
        self.assertTrue(shift.name == shift21.name)
        self.assertTrue(shift.work_mode == shift21.work_mode)

        shift = shift.prev()
        start = self.prev_day + self.H08
        end = self.prev_day + self.H20
        self.assertTrue((shift.start_time, shift.end_time) == (start, end))
        self.assertTrue(shift.id == shift.pk)
        self.assertTrue(shift.id == shift22.id)
        self.assertTrue(shift.name == shift22.name)
        self.assertTrue(shift.work_mode == shift22.work_mode)

    def test_prev(self):
        shift21 = models.WorkShift.objects.create(
            work_mode=self.wm2, name='TestWorkShift1', number=1, start=self.N20, end=self.N08)
        shift22 = models.WorkShift.objects.create(
            work_mode=self.wm2, name='TestWorkShift2', number=2, start=self.N08, end=self.N20)

        shift = shift21.work_shift(self.next_day + self.H20)

        n = 0
        while n < 5:
            shift = shift.prev()
            n += 1

        start = self.prev_day + self.H08
        end = self.prev_day + self.H20
        self.assertTrue((shift.start_time, shift.end_time) == (start, end))
        self.assertTrue(shift.id == shift.pk)
        self.assertTrue(shift.id == shift22.id)
        self.assertTrue(shift.name == shift22.name)
        self.assertTrue(shift.work_mode == shift22.work_mode)

        shift = shift21.work_shift(self.next_day + self.H20)

        while shift.start_time > self.prev_day + self.H08:
            shift = shift.prev()

        start = self.prev_day + self.H08
        end = self.prev_day + self.H20
        self.assertTrue((shift.start_time, shift.end_time) == (start, end))
        self.assertTrue(shift.id == shift.pk)
        self.assertTrue(shift.id == shift22.id)
        self.assertTrue(shift.name == shift22.name)
        self.assertTrue(shift.work_mode == shift22.work_mode)
