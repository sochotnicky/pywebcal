import sys
import StringIO
from dateutil.tz import tzical

from icalendar import Calendar, Event, Timezone
from icalendar.prop import vDatetime
from webdav.WebdavClient import CollectionStorer,ResourceStorer
import datetime

class WebCal(object):

    def __init__(self, webdavURL, username, password):
        self._webdavURL = webdavURL
        self._username = username
        self._password = password
        self.connection = None

    def connect(self):
        if self._webdavURL[-4:] == '.ics':
            self.connection = ResourceStorer(self._webdavURL, validateResourceNames=False)
        else:
            self.connection = CollectionStorer(self._webdavURL, validateResourceNames=False)
        self.connection.connection.addBasicAuthorization(self._username, self._password)

    def get_calendar_uids(self):
        if not self.connection:
            self.connect()
        if type(self.connection) == ResourceStorer:
            return [0]
        resources = self.connection.listResources()
        ret = []
        for k in resources.keys():
            fname = k.rpartition('/')[2]
            ret.append(fname)
        return ret

    def get_calendar(self, uid):
        if not self.connection:
            self.connect()
        if uid == 0:
            rs = self.connection
        else:
            rs = self.connection.getResourceStorer(uid)
        c = Calendar.from_string(rs.downloadContent().read())
        return c

class ICal(object):
    def __init__(self, calendar):
        self.ical = calendar
        self.fileobj = StringIO.StringIO(str(self.ical))

    def get_event_ids(self):
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
        event = self._get_event(uid);
        return event['LOCATION']

    def set_location(self, uid, location):
        event = self._get_event(uid)
        event['LOCATION'] = location

    def get_timezones(self):
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
        event = self._get_event(uid);
        strDT = str(event[compname])
        # this should be fixed in icalendar (only date specified => fails)
        if len(strDT) == 8:
            strDT = "%s000000" % strDT
        dt = vDatetime.from_ical(strDT)
        if len(strDT) == 16: # UTC time
            return dt
        else:
            return self._get_tz_datetime(event[compname], dt)

    def _set_datetime(self, uid, compname, dt):
        event = self._get_event(uid);
        vdt = vDatetime(dt)
        event[compname] = vdt.ical()

    def _get_tz_datetime(self, component, dt):

        if hasattr(component, 'params') and str(component.params)[0:4] == 'TZID':
            tzname = str(component.params)[5:]
        else:
            tzname = self.get_timezones()[0]
        # we should read all timezones in the beginning
        # and cache them
        tz = tzical(self.fileobj).get(tzname)
        self.fileobj.seek(0)
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
