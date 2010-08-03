# Copyright 2010  Red Hat, Inc.
# Stanislav Ochotnicky <sochotnicky@redhat.com>
#
# This file is part of pywebcal.
#
# pywebcal is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pywebcal is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pywebcal.  If not, see <http://www.gnu.org/licenses/>.

from pywebcal import ICal
import unittest

from icalendar import Calendar
from datetime import tzinfo, timedelta, datetime


class ICalTest(unittest.TestCase):
    testFile = 'test.ics'

    def setUp(self):
        c = Calendar.from_string(open("test.ics","r").read())
        self.ical = ICal(c)

    def test_get_event_ids(self):
        ids = self.ical.get_event_ids()
        self.assertEqual(32, len(ids))

    def test_datetime(self):
        ids = self.ical.get_event_ids()
        dts1 = datetime(2010, 8, 13, 0, 0, 0, 0, UTC())
        dtsret1 = self.ical.get_start_datetime(ids[0])
        self.assertEqual(dts1, dtsret1)

        dte1 = datetime(2010, 8, 14, 23, 59, 0, 0, UTC())
        dteret1 = self.ical.get_end_datetime(ids[0])
        self.assertEqual(dte1, dteret1)

        dts1 = datetime(2010, 8, 13, 0, 0, 0, 0)
        dtsret1 = self.ical.get_start_datetime(ids[0])
        # comparing tz-aware and unaware dates
        self.assertRaises(TypeError, lambda(x,y): x == y, dts1, dtsret1)

        self.ical.set_end_datetime(ids[0], dteret1 + timedelta(hours=1))
        dte1new = datetime(2010, 8, 15, 0, 59, 0, 0, UTC())
        dteret1new = self.ical.get_end_datetime(ids[0])
        self.assertEqual(dte1new, dteret1new)

    def test_summary(self):
        ids = self.ical.get_event_ids()
        sum_first = 'Grape Festival 2010'
        sum_last = 'Blind Guardian + Enforcer + more at Gasometer'
        self.assertEqual(sum_first, self.ical.get_summary(ids[0]))
        self.assertEqual(sum_last, self.ical.get_summary(ids[-1]))

        sum_test = 'Testing sum'
        self.ical.set_summary(ids[0], sum_test)
        self.assertEqual(sum_test, self.ical.get_summary(ids[0]))
        self.assertEqual(sum_last, self.ical.get_summary(ids[-1]))

    def test_location(self):
        ids = self.ical.get_event_ids()
        loc_first = 'Letisko, Slovakia'
        loc_last = 'Gasometer, Austria'
        self.assertEqual(loc_first, self.ical.get_location(ids[0]))
        self.assertEqual(loc_last, self.ical.get_location(ids[-1]))

    def test_events_dates(self):
        before = self.ical.events_before(datetime(2010, 7, 10, 0, 0, 0, 0, UTC()))
        self.assertEqual(0, len(before))

        before = self.ical.events_before(datetime(2010, 12, 7, 0, 0, 0, 0, UTC()))
        self.assertEqual(32, len(before))

        before = self.ical.events_before(datetime(2010, 10, 3, 0, 0, 0, 0, UTC()))
        self.assertEqual(12, len(before))

        between = self.ical.events_between(
            datetime(2010, 8, 20, 0, 0, 0, 0, UTC()),
            datetime(2010, 8, 24, 0, 0, 0, 0, UTC()))
        self.assertEqual(0, len(between))

        between = self.ical.events_between(
            datetime(2010, 8, 12, 0, 0, 0, 0, UTC()),
            datetime(2010, 8, 24, 0, 0, 0, 0, UTC()))
        self.assertEqual(2, len(between))

        after = self.ical.events_after(datetime(2010, 7, 10, 0, 0, 0, 0, UTC()))
        self.assertEqual(32, len(after))

        after = self.ical.events_after(datetime(2010, 8, 20, 0, 0, 0, 0, UTC()))
        self.assertEqual(26, len(after))

        after = self.ical.events_after(datetime(2010, 12, 7, 0, 0, 0, 0, UTC()))
        self.assertEqual(0, len(after))



ZERO = timedelta(0)
HOUR = timedelta(hours=1)

# A UTC class.

class UTC(tzinfo):
    """UTC"""

    def utcoffset(self, dt):
        return ZERO

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return ZERO

utc = UTC()

if __name__ == '__main__':
    unittest.main()
