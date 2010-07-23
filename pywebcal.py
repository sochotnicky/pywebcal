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
        self.connection = CollectionStorer(self._webdavURL, validateResourceNames=False)
        self.connection.connection.addBasicAuthorization(self._username, self._password)
        self.connection.validate()

    def get_calendar_uids(self):
        if not self.connection:
            self.connect()
        resources = self.connection.listResources()
        ret = []
        for k in resources.keys():
            fname = k.rpartition('/')[2]
            ret.append(fname)
        print ret
        return ret

    def get_calendar(self, uid):
        if not self.connection:
            self.connect()
        rs = self.connection.getResourceStorer(uid)
        c = Calendar.from_string(rs.downloadContent().read())
        return c

class ICal(object):
    def __init__(self, calendar):
        self.ical = calendar
        self.fileobj = StringIO.StringIO(str(self.ical))

    def get_summary(self):
        for event in self.ical.walk('VEVENT'):
            return event['SUMMARY']
        raise Exception("No VEVENT found!")

    def set_summary(self, summary):
        for event in self.ical.walk('VEVENT'):
            event['SUMMARY'] = summary
            return
        raise Exception("No VEVENT found!")

    def get_start_datetime(self):
        return self._get_datetime("DTSTART")

    def set_start_datetime(self, dt):
        return self._set_datetime("DTSTART", dt)

    def get_end_datetime(self):
        return self._get_datetime("DTEND")

    def set_end_datetime(self, dt):
        return self._set_datetime("DTEND", dt)

    def getDescription(self):
        for event in self.ical.walk('VEVENT'):
            return event['DESCRIPTION']
        raise Exception("No VEVENT found!")

    def setDescription(self, description):
        for event in self.ical.walk('VEVENT'):
            event['DESCRIPTION'] = description
            return
        raise Exception("No VEVENT found!")

    def _get_datetime(self, compname):
        for event in self.ical.walk('VEVENT'):
            dt = vDatetime.from_ical(str(event[compname]))
            return self._get_tz_datetime(event[compname], dt)
        raise Exception("No VEVENT found!")

    def _set_datetime(self, compname, dt):
        for event in self.ical.walk('VEVENT'):
            vdt = vDatetime(dt)
            event[compname] = vdt.ical()
            return
        raise Exception("No VEVENT found!")

    def _get_tz_datetime(self, component, dt):
        tzname = str(component.params)[5:]
        tz = tzical(self.fileobj).get(tzname)
        return datetime.datetime(dt.year, dt.month, dt.day,
                                 dt.hour, dt.minute, dt.second,
                                 0, tz)

#wc = WebCal('https://somewhere.com/dav/Calendar',
#            'name', 'password')

#ids = wc.get_calendar_uids()
#print ids[2]
#c = wc.get_calendar(ids[2])

c = Calendar.from_string(open("test.ics","r").read())
ic = ICal(c)
print ic.get_summary()
ic.set_summary('blah')
print ic.get_summary()
print c.walk('VEVENT')[0].keys()
print c
dt =  ic.get_start_datetime()
print dt
ic.set_start_datetime(dt+datetime.timedelta(days=1))
print c

