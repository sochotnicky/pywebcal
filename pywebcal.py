import sys
import StringIO
import datetime

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
python webdav library (http://sourceforge.net/projects/pythonwebdavlib/)"""
    sys.exit(1)

class WebCal(object):
    """
    Class providing simple access to iCal calendars over WebDAV

    """

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

    def get_calendar_uids(self):
        """get_calendar_uids() -> [uid, uid1, ...]

        Returns list of calendar UIDs in collection. If the webdav URL
        points to single iCal file, list with one UID 0 is returned
        """
        if not self.connection:
            self._connect()
        if type(self.connection) == ResourceStorer:
            return [0]
        resources = self.connection.listResources()
        ret = []
        for k in resources.keys():
            fname = k.rpartition('/')[2]
            ret.append(fname)
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
        c = Calendar.from_string(rs.downloadContent().read())
        return c

    def _connect(self):
        if self._webdavURL[-4:] == '.ics':
            self.connection = ResourceStorer(self._webdavURL, validateResourceNames=False)
        else:
            self.connection = CollectionStorer(self._webdavURL, validateResourceNames=False)

        if self._username and self._password:
            self.connection.connection.addBasicAuthorization(self._username, self._password)


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

    def events_after(self, dt):
        """events_after(datetime) -> [(datetime, uid), (datetime1, uid1), ...]

        Returns list of tuples of (datetime.datetime, Event UID)
        where datetime represents date of nearest occurrence of given
        event after dt datetime object
        """
        eafter = []
        eids = self.get_event_ids()
        for eid in eids:
            rule = self.get_rrule(eid)
            if not rule:
                sdate = self.get_start_datetime(eid)
                if dt < sdate:
                    eafter.append((sdate, eid))
            else:
                d = rule.after(dt, inc=True)
                eafter.append((d, eid))
        return eafter

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

#wc = WebCal('https://somewhere.com/dav/Calendar',
#            'name', 'password')

#ids = wc.get_calendar_uids()
#print ids[0]
#c = wc.get_calendar(ids[0])
#print c

c = Calendar.from_string(open("test.ics","r").read())
ic = ICal(c)
ids = ic.get_event_ids()
i = ids[0]
print ic.get_summary(i)
ic.set_summary(i, 'blah')
print ic.get_summary(i)
print c.walk('VEVENT')[0].keys()
print c
dt =  ic.get_start_datetime(i)
print dt
ic.set_start_datetime(i, dt+datetime.timedelta(days=1))
print c
print len(ids)

print "Summary: %s" % ic.get_summary(i)
print "Start: %s" % ic.get_start_datetime(i)
print "End: %s" % ic.get_end_datetime(i)
print "Location: %s" % ic.get_location(i)

print ic.events_after(datetime.datetime(2010,07,10,0,0,0,0,gettz()))
