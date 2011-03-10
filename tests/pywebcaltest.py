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

import vobject
from datetime import tzinfo, timedelta, datetime


class ICalTest(unittest.TestCase):

    def setUp(self):
        c = vobject.base.readComponents(open("test.ics","r")).next()
        self.ical = ICal(c)
        c = vobject.base.readComponents(open("test2.ics","r")).next()
        self.ical2 = ICal(c)

    def test_get_event_ids(self):
        ids = self.ical.get_event_ids()
        self.assertEqual(32, len(ids))
        ids = self.ical2.get_event_ids()
        self.assertEqual(1, len(ids))

    def test_get_events(self):
        r = self.ical.get_events()
        self.assertEqual(32, len(r))

    def test_datetime(self):
        ids = self.ical.get_events()
        dts1 = datetime(2010, 8, 13, 0, 0, 0, 0, UTC())
        dtsret1 = ids[0].get_start_datetime()
        self.assertEqual(dts1, dtsret1)

        dte1 = datetime(2010, 8, 14, 23, 59, 0, 0, UTC())
        dteret1 = ids[0].get_end_datetime()
        self.assertEqual(dte1, dteret1)

        dts1 = datetime(2010, 8, 13, 0, 0, 0, 0)
        dtsret1 = ids[0].get_start_datetime()
        # comparing tz-aware and unaware dates
        self.assertRaises(TypeError, lambda(x,y): x == y, dts1, dtsret1)

        ids[0].set_end_datetime(dteret1 + timedelta(hours=1))
        ids = self.ical.get_events()
        dte1new = datetime(2010, 8, 15, 0, 59, 0, 0, UTC())
        dteret1new = ids[0].get_end_datetime()
        self.assertEqual(dte1new, dteret1new)

    def test_summary(self):
        ids = self.ical.get_events()
        sum_first = 'Grape Festival 2010'
        sum_last = 'Blind Guardian + Enforcer + more at Gasometer'
        self.assertEqual(sum_first, ids[0].get_summary())
        self.assertEqual(sum_last, ids[-1].get_summary())

        sum_test = 'Testing sum'
        ids[0].set_summary(sum_test)
        ids = self.ical.get_events()
        self.assertEqual(sum_test, ids[0].get_summary())
        self.assertEqual(sum_last, ids[-1].get_summary())

    def test_location(self):
        ids = self.ical.get_events()
        loc_first = 'Letisko, Slovakia'
        loc_last = 'Gasometer, Austria'
        self.assertEqual(loc_first, ids[0].get_location())
        self.assertEqual(loc_last, ids[-1].get_location())

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

    def test_url(self):
        ids = self.ical.get_events()
        url = ids[0].get_url()
        self.assertEqual(url, "http://www.last.fm/festival/1416224+Grape+Festival+2010")

        url = ids[-1].get_url()
        self.assertEqual(url, "http://www.last.fm/event/1328092+Blind+Guardian+at+Gasometer+on+16+October+2010")

    def test_attendees(self):
        ids = self.ical2.get_events()
        at = ids[0].get_attendees()
        self.assertEquals(2, len(at))
        self.assertEquals(u"Milgrim", at[0].name)
        self.assertEquals("mailto:milgrim@junkie.me", at[0].address)
        self.assertEquals("REQ-PARTICIPANT", at[0].role)
        self.assertEquals("TRUE", at[0].rsvp_request)
        self.assertEquals("NEEDS-ACTION", at[0].rsvp_status)
        self.assertEquals(str(at[0]), "ATTENDEE;RSVP=TRUE;ROLE=REQ-PARTICIPANT;CN=Milgrim;PARTSTAT=NEEDS-ACTION:m\r\n ailto:milgrim@junkie.me\r\n")


        self.assertEquals("Idoru", at[1].name)
        self.assertEquals("mailto:idoru@virtual.me", at[1].address)
        self.assertEquals("REQ-PARTICIPANT", at[1].role)
        self.assertEquals("TRUE", at[1].rsvp_request)
        self.assertEquals("DECLINED", at[1].rsvp_status)
        self.assertEquals(str(at[1]), "ATTENDEE;RSVP=TRUE;ROLE=REQ-PARTICIPANT;CN=Idoru;PARTSTAT=DECLINED:mailto:\r\n idoru@virtual.me\r\n")



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
