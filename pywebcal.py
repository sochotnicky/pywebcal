import sys
import StringIO
import datetime
import logging
import pickle
from os import path, environ

try:
    from dateutil.tz import tzical, gettz
    from dateutil.rrule import rrulestr
except ImportError:
    print """You miss dependencies for running this library. Please
install dateutil module (python-dateutil)."""
    sys.exit(1)

try:
    from icalendar import Calendar, Event, Timezone
    from icalendar.prop import vDatetime
except ImportError:
    print """You miss dependencies for running this library. Please
install icalendar module (python-icalendar). You can find sources of
icalendar on http://codespeak.net/icalendar/. Or install it with
`easy_install icalendar`"""
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
        """get_calendar(uid) -> icalendar.Calendar

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
            c = cc[1]
        else:
            c = Calendar.from_string(rs.downloadContent().read())
            self.__set_cached_calendar(uid, c, modified)
        return c

    def _connect(self):
        if self._webdavURL[-4:] == '.ics':
            self.connection = ResourceStorer(self._webdavURL, validateResourceNames=False)
        else:
            self.connection = CollectionStorer(self._webdavURL, validateResourceNames=False)

        if self._username and self._password:
            self.connection.connection.addBasicAuthorization(self._username, self._password)

        self.connection.connection.logger.setLevel(logging.WARNING)

    def __set_cached_calendar(self, uid, calendar, modified):
        if not self._cache:
            self.__load_cache()

        if self._cache.has_key(uid) and self._cache[uid][0] == modified:
            return

        self._cache[uid] = (modified, calendar)
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
        cacheFile = open(self._cache_file, 'r')
        self._cache = pickle.load(cacheFile)
        cacheFile.close()

    def __save_cache(self):
        cacheFile = open(self._cache_file, 'w')
        pickle.dump(self._cache, cacheFile)
        cacheFile.close()

class ICal(object):
    """High-level interface for working with iCal files"""

    def __init__(self, calendar):
        """Initializes class with given icalendar.Calendar instance
        """
        self.ical = calendar

        fileobj = StringIO.StringIO(str(self.ical))
        self._tzical = tzical(fileobj)

    def get_event_ids(self):
        """get_event_ids() -> [uid, uid1, ...]

        Returns UIDs of all VEVENTs defined in iCal instance. These
        UIDs are used for access to concrete events defined within
        iCal file"""
        uids = []
        for event in self.ical.walk('VEVENT'):
            uids.append(event['UID'])
        return uids

    def get_summary(self, uid):
        return str(self._get_event(uid)['SUMMARY'])

    def set_summary(self, uid, summary):
        event = self._get_event(uid)
        event['SUMMARY'] = summary

    def get_start_datetime(self, uid):
        return self._get_datetime(uid, "DTSTART")

    def set_start_datetime(self, uid, dt):
        return self._set_datetime(uid, "DTSTART", dt)

    def get_end_datetime(self, uid):
        return self._get_datetime(uid, "DTEND")

    def set_end_datetime(self, uid, dt):
        return self._set_datetime(uid, "DTEND", dt)

    def get_description(self, uid):
        event = self._get_event(uid)
        return event['DESCRIPTION']

    def set_description(self, uid, description):
        event = self._get_event(uid)
        event['DESCRIPTION'] = description

    def get_location(self, uid):
        event = self._get_event(uid)
        return event['LOCATION']

    def set_location(self, uid, location):
        event = self._get_event(uid)
        event['LOCATION'] = location

    def get_rrule(self, uid):
        """get_rrule(uid) -> dateutil.rrule

        Returns RRULE defined for given event or None if
        no RRULE has been defined

        uid - Event UID for which rrule should be returned
        """
        try:
            ret = None
            rrule_str = self.get_rrule_str(uid)
            ret = rrulestr(rrule_str, dtstart=self.get_start_datetime(uid))
        except ValueError:
            pass
        finally:
            return ret

    def get_rrule_str(self, uid):
        """get_rrule_str(uid) -> string

        Returns string representation of repeat rule for given event
        """
        event = self._get_event(uid)
        return str(event['RRULE'])

    def events_before(self, dt):
        """events_before(datetime) -> [(datetime, uid), (datetime1, uid1), ...]

        Returns list of tuples of (datetime.datetime, Event UID)
        where datetime represents date of nearest occurrence (start) of given
        event before dt datetime object
        """
        ret = []
        eids = self.get_event_ids()
        for eid in eids:
            rule = self.get_rrule(eid)
            if not rule:
                sdate = self.get_start_datetime(eid)
                if dt >= sdate:
                    ret.append((sdate, eid))
            else:
                d = rule.before(dt, inc=True)
                ret.append((d, eid))
        return ret

    def events_between(self, dtstart, dtend):
        """events_before(datetime) -> [(datetime, uid), (datetime1, uid1), ...]

        Returns list of tuples of (datetime.datetime, Event UID)
        where datetime represents date of occurrence (start) of given
        event between dtstart and dtend datetime objects
        """
        ret = []
        eids = self.get_event_ids()
        for eid in eids:
            rule = self.get_rrule(eid)
            if not rule:
                sdate = self.get_start_datetime(eid)
                if dtstart <= sdate <= dtend:
                    ret.append((sdate, eid))
            else:
                d = rule.between(dtstart, dtend, inc=True)
                ret.append((d, eid))
        return ret

    def events_after(self, dt):
        """events_after(datetime) -> [(datetime, uid), (datetime1, uid1), ...]

        Returns list of tuples of (datetime.datetime, Event UID)
        where datetime represents date of nearest occurrence (start) of given
        event after dt datetime object
        """
        ret = []
        eids = self.get_event_ids()
        for eid in eids:
            rule = self.get_rrule(eid)
            if not rule:
                sdate = self.get_start_datetime(eid)
                if dt <= sdate:
                    ret.append((sdate, eid))
            else:
                d = rule.after(dt, inc=True)
                ret.append((d, eid))
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

    def _get_event(self, uid):
        for event in self.ical.walk('VEVENT'):
            if event['UID'] == uid:
                return event
        raise Exception("No VEVENT with UID %s found" % uid)

    def _get_datetime(self, uid, compname):
        """_get_datetime(uid, compname) -> datetime

        Returns TZ aware datetime object from given sub-component
        (DTSTART, DTEND, etc) of given VEVENT identified by uid.
        """
        event = self._get_event(uid)
        strDT = str(event[compname])
        # this should be fixed in icalendar (only date specified => fails)
        if len(strDT) == 8:
            strDT = "%s000000" % strDT

        # unfortunately vDatetime.from_ical is not TZ aware (ignores
        # TZIDs defined in dates/times). We need to fix this...
        dt = vDatetime.from_ical(strDT)
        if len(strDT) == 16: # UTC time
            return dt
        else:
            return self._get_tz_datetime(event[compname], dt)

    def _set_datetime(self, uid, compname, dt):
        event = self._get_event(uid)
        vdt = vDatetime(dt)
        event[compname] = vdt.ical()

    def _get_tz_datetime(self, component, dt):
        if hasattr(component, 'params') and str(component.params)[0:4] == 'TZID':
            tzname = str(component.params)[5:]
        else:
            tzids = self.get_timezones()
            if len(tzids) == 0:
                raise Exception("Time of %s component is not in UTC" \
                                "and no VTIMEZONEs have been defined!" \
                                " Bailing out" % str(component) )
            tzname = tzids[0]

        tz = self._tzical.get(tzname)
        return datetime.datetime(dt.year, dt.month, dt.day,
                                 dt.hour, dt.minute, dt.second,
                                 0, tz)
