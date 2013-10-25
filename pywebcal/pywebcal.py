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

import sys
import StringIO
import datetime
import logging
import pickle
import hashlib
from os import path, environ

try:
    from dateutil.tz import tzical, gettz
    from dateutil.rrule import rrulestr
except ImportError:
    print """You miss dependencies for running this library. Please
install dateutil module (python-dateutil)."""
    sys.exit(1)

try:
    import vobject
except ImportError:
    print """You miss dependencies for running this library. Please
install vobject module (python-vobject). You can find sources of
vobject on http://vobject.skyhouseconsulting.com/. Or install it with
`easy_install vobject`"""
    sys.exit(1)

try:
    from webdav.WebdavClient import CollectionStorer,ResourceStorer
except ImportError:
    print """You miss dependencies for running this library. Please
install python webdav library (https://code.launchpad.net/python-webdav-lib/)"""
    sys.exit(1)

class WebCal(object):
    """
    Class providing simple cached access to iCal calendars over WebDAV

    """
    _cache_file = '%s/.pywebcal.cache' % environ['HOME']

    def __init__(self, webdavURL, username = None, password = None):
        """webdavURL - URL of webdav calendar. For example
                    http://www.google.com/calendar/ical/9e11j73ff4pdomjlort7v10h640okf47%40import.calendar.google.com/public/basic.ics
        username - provide username in case it is needed
        password - password to access calendar
        """
        self._webdavURL = webdavURL
        self._username = username
        self._password = password
        self.connection = None
        self._modifiedTimes = {}
        self._cache = None
        self._connID = ConnID(webdavURL, username)
        self._cache_file = "%s.%s" % (self._cache_file, self._connID.digest)

    def get_calendar_uids(self):
        """get_calendar_uids() -> [uid, uid1, ...]

        Returns list of calendar UIDs in collection. If the webdav URL
        points to single iCal file, list with one UID 0 is returned
        """
        if not self.connection:
            self._connect()
        if type(self.connection) == ResourceStorer:
            self._modifiedTimes[0] = datetime.datetime.now(gettz())
            return [0]
        resources = self.connection.listResources()
        ret = []
        for k in resources.keys():
            fname = k.rpartition('/')[2]
            ret.append(fname)
            tm = resources[k].getLastModified()
            self._modifiedTimes[fname] = datetime.datetime(tm.tm_year, tm.tm_mon, tm.tm_mday,
                                                           tm.tm_hour, tm.tm_min, tm.tm_sec, 0,
                                                           gettz("UTC"))
        return ret

    def get_calendar(self, uid):
        """get_calendar(uid) -> ICal

        Returns Calendar instance from webdav URL identified by uid.
        """
        if not self.connection:
            self._connect()
        if uid == 0:
            rs = self.connection
        else:
            rs = self.connection.getResourceStorer(uid)
        modified = self._modifiedTimes[uid]
        cc = self.__get_cached_calendar(uid)
        if cc and cc[0] == modified: # calendar is cached
            data = cc[1]
            vcal = vobject.base.readComponents(StringIO.StringIO(data[0])).next()
            c = ICal(vcal)
        else:
            vcal = vobject.base.readComponents(rs.downloadContent().read()).next()
            c = ICal(vcal)
            self.__set_cached_calendar(uid, modified, (vcal.serialize(),))
        return c

    def get_all_events(self):
        """get_all_events() -> [Event, Event1,...]

        Returns all events in all calendars for this connection"""
        if not self.connection:
            self._connect()
        events = []
        for calid in self.get_calendar_uids():
            cal = self.get_calendar(caldid)
            events.extend(cal.get_events())
        return ret

    def _connect(self):
        if self._webdavURL[-4:] == '.ics':
            self.connection = ResourceStorer(self._webdavURL, validateResourceNames=False)
        else:
            self.connection = CollectionStorer(self._webdavURL, validateResourceNames=False)

        if self._username and self._password:
            self.connection.connection.addBasicAuthorization(self._username, self._password)

        self.connection.connection.logger.setLevel(logging.WARNING)

    def __set_cached_calendar(self, uid, modified, data):
        if not self._cache:
            self.__load_cache()

        if self._cache.has_key(uid) and self._cache[uid][0] == modified:
            return

        self._cache[uid] = (modified, data)
        self.__save_cache()

    def __get_cached_calendar(self, uid):
        if not self._cache:
            self.__load_cache()

        if self._cache and self._cache.has_key(uid):
            return self._cache[uid]
        else:
            return None

    def __load_cache(self):
        if not path.isfile(self._cache_file) or path.getsize(self._cache_file) == 0:
            self._cache = {}
            return
        with open(self._cache_file, 'r') as cacheFile:
            self._cache = pickle.load(cacheFile)

    def __save_cache(self):
        with open(self._cache_file, 'w') as cacheFile:
            pickle.dump(self._cache, cacheFile)

class ICal(object):
    """High-level interface for working with iCal files"""

    def __init__(self, vobj):
        """Initializes class with given vobject.icalendar.VCalendar2_0
        instance
        """
        self.ical = vobj

    def get_event_ids(self):
        """get_event_ids() -> [uid, uid1, ...]

        Returns UIDs of all VEVENTs defined in iCal instance. These
        UIDs are used for access to concrete events defined within
        iCal file"""
        uids = []
        try:
            for event in self.ical.vevent_list:
                uids.append(event.uid.value)
        except AttributeError, e:
            # this means ical has no events, maybe just todos?
            # one way or the other -> ignore and return empty list
            pass
        return uids

    def get_events(self):
        """get_events() -> [Event, Event1, ...]

        Returns Event classes defined in iCal instance.
        """
        ret = []
        try:
            for event in self.ical.vevent_list:
                ret.append(Event(self.ical, event))
        except AttributeError, e:
            # this means ical has no events, maybe just todos?
            # one way or the other -> ignore and return empty list
            pass
        return ret

    def events_before(self, dt):
        """events_before(datetime) -> [(datetime, Event), (datetime1, Event1), ...]

        Returns list of tuples of (datetime.datetime, Event)
        where datetime represents date of nearest occurrence (start) of given
        event before dt datetime object
        """
        ret = []
        es = self.get_events()
        # prepare timeless date in case it's needed
        d = dt.date()
        for e in es:
            rule = e.get_rrule()
            if not rule:
                sdate = e.get_start_datetime()
                if type(sdate) == datetime.date:
                    cmpdate = d
                else:
                    cmpdate = dt
                if cmpdate >= sdate:
                    ret.append((sdate, e))
            else:
                d = rule.before(dt, inc=True)
                if d:
                    ret.append((d, e))
        return ret

    def events_between(self, dtstart, dtend):
        """events_before(datetime) -> [(datetime, Event), (datetime1, Event1), ...]

        Returns list of tuples of (datetime.datetime, Event UID)
        where datetime represents date of occurrence (start) of given
        event between dtstart and dtend datetime objects
        """
        ret = []
        es = self.get_events()
        # prepare timeless starts-stops
        dstart, dend = dtstart.date(), dtend.date()
        for e in es:
            rule = e.get_rrule()
            if not rule:
                sdate = e.get_start_datetime()
                if type(sdate) == datetime.date:
                    cmpstart, cmpend = dstart, dend
                else:
                    cmpstart, cmpend = dtstart, dtend

                if cmpstart <= sdate <= cmpend:
                    ret.append((sdate, e))
            else:
                d = rule.between(dtstart, dtend, inc=True)
                if d:
                    ret.append((d, e))
        return ret

    def events_after(self, dt):
        """events_after(datetime) -> [(datetime, Event), (datetime1, Event1), ...]

        Returns list of tuples of (datetime.datetime, Event UID)
        where datetime represents date of nearest occurrence (start) of given
        event after dt datetime object
        """
        ret = []
        es = self.get_events()
        # prepare timeless date in case it's needed
        d = dt.date()
        for e in es:
            rule = e.get_rrule()
            if not rule:
                sdate = e.get_start_datetime()
                if type(sdate) == datetime.date:
                    cmpdate = d
                else:
                    cmpdate = dt
                if cmpdate <= sdate:
                    ret.append((sdate, e))
            else:
                d = rule.after(dt, inc=True)
                if d:
                    ret.append((d, e))
        return ret

    def get_timezones(self):
        """get_timezones() -> [TZID, TZID1, ...]

        Returns list of all TZIDS defined in iCal file or empty list
        if no TZIDs have been defined (all times are in UTC). TZID is for
        example 'Europe/Berlin'
        """
        tzids = []
        for tz in self.ical.walk('VTIMEZONE'):
            tzids.append(tz['TZID'])
        return tzids

class Event(object):
    def __init__(self, ical, event):
        """__init__(ical, vevent) -> Event

        ical - iCal text for the event
        event - vevent instance representing given event
        """
        self.uid = event.uid.value
        self.ical = ical
        self._event = event

    def get_summary(self):
        """get_summary() -> str

        Returns string representing summary of event
        """
        return self._event.summary.value

    def set_summary(self, summary):
        """set_summary(str)

        Sets summary to text provided
        """
        self._event.summary.value = summary

    def get_start_datetime(self):
        """get_start_datetime() -> datetime.datetime or datetime.date

        This returns start date of the event or datetime in case time
        is included. This should probably be fixed to return datetime
        always."""
        return self._event.dtstart.value

    def set_start_datetime(self, dt):
        """set_start_datetime(dt)

        Sets start datetime to provided datetime.datetime instance"""
        self._event.dtstart.value = dt

    def get_end_datetime(self):
        """get_end_datetime() -> datetime.datetime or datetime.date

        This returns end date of the event or datetime in case time
        is included. This should probably be fixed to return datetime
        always."""
        return self._event.dtend.value

    def set_end_datetime(self, dt):
        """set_end_datetime(dt)

        Sets end datetime to provided datetime.datetime instance"""
        self._event.dtend.value = dt

    def get_description(self):
        """get_description() -> str

        Returns long description of the event"""
        event = self._event
        return event['DESCRIPTION']

    def set_description(self, description):
        """set_description(description)

        Sets long description of the event"""
        self._event['DESCRIPTION'] = description

    def get_location(self):
        """get_location() -> str

        Returns event location text (where it is going to happen)"""
        return self._event.location.value

    def set_location(self, location):
        """set_location(location)

        Sets location text of the event"""
        self._event.location.value = location

    def get_url(self):
        """get_url() -> str

        Returns event url text"""
        return self._event.url.value

    def set_url(self, url):
        """set_url(location)

        Sets url text of the event"""
        self._event.url.value = url

    def get_attendees(self):
        """get_attendees() -> [Attendee]

        Returns list of Attendee classes representing event attendees
        and their statuses"""
        ret = []
        for at in self._event.attendee_list:
            ret.append(Attendee(at))
        return ret

    def set_attendees(self, atlist):
        self._event.attendee_list = atlist

    def get_rruleset(self):
        """get_rruleset(uid) -> dateutil.rrule.rruleset

        Returns RRULESET defined for given event or None if
        no RRULESET has been defined

        uid - Event UID for which rrule should be returned
        """
        return self._event.getrruleset()


class Attendee(object):

    possible_params = [('CN', 'name'),
                       ('ROLE', 'role'),
                       ('RSVP', 'rsvp_request'),
                       ('PARTSTAT','rsvp_status'),
        ]


    def __init__(self, ical_attendee):
        self.address = ical_attendee.value
        self.__ical = ical_attendee
        self.params = self.__ical.params
        for a, b in self.possible_params:
            self.__set_param(a, b)

    def __set_param(self, paramname, propname=None):
        if self.params.has_key(paramname):
            if not propname:
                propname = paramname
            setattr(self, propname, self.params[paramname][0])

    def __str__(self):
        return self.__ical.serialize()

class ConnID(object):
    """Class that holds unique connection ID so that we can identify connections"""

    def __init__(self, url, login = None):
        digest = hashlib.md5()
        digest.update(url)
        if login:
            digest.update(login)

        self.digest = digest.hexdigest()
        self.url = url
        self.login = login
