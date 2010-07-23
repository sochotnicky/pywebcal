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
        self.connection = CollectionStorer(webdavUrl, validateResourceNames=False)
        self.connection.connection.addBasicAuthorization(username, password)
        self.connection.validate()

    def getCalendarUIDs(self):
        if not self.connection:
            self.connect()
        resources = self.connection.listResources()
        ret = []
        for k in resources.keys():
            fname = k.rpartition('/')[2]
            ret.append(fname)
        print ret
        return ret

    def getCalendar(self, uid):
        if not self.connection:
            self.connect()
        rs = self.connection.getResourceStorer(uid)
        c = Calendar.from_string(rs.downloadContent().read())
        return c

class ICal(object):
    def __init__(self, calendar):
        self.ical = calendar
        self.fileobj = StringIO.StringIO(str(self.ical))

    def getSummary(self):
        for event in self.ical.walk('VEVENT'):
            return event['SUMMARY']
        raise Exception("No VEVENT found!")

    def setSummary(self, summary):
        for event in self.ical.walk('VEVENT'):
            event['SUMMARY'] = summary
            return
        raise Exception("No VEVENT found!")

    def getStartDateTime(self):
        return self._getDateTime("DTSTART")

    def setStartDateTime(self, dt):
        return self._setDateTime("DTSTART", dt)

    def getEndDateTime(self):
        return self._getDateTime("DTEND")

    def setEndDateTime(self, dt):
        return self._setDateTime("DTEND", dt)

    def getDescription(self):
        for event in self.ical.walk('VEVENT'):
            return event['DESCRIPTION']
        raise Exception("No VEVENT found!")

    def setDescription(self, description):
        for event in self.ical.walk('VEVENT'):
            event['DESCRIPTION'] = description
            return
        raise Exception("No VEVENT found!")

    def _getDateTime(self, compname):
        for event in self.ical.walk('VEVENT'):
            dt = vDatetime.from_ical(str(event[compname]))
            return self._getTZDateTime(event[compname], dt)
        raise Exception("No VEVENT found!")

    def _setDateTime(self, compname, dt):
        for event in self.ical.walk('VEVENT'):
            vdt = vDatetime(dt)
            event[compname] = vdt.ical()
            return
        raise Exception("No VEVENT found!")

    def _getTZDateTime(self, component, dt):
        tzname = str(component.params)[5:]
        tz = tzical(self.fileobj).get(tzname)
        return datetime.datetime(dt.year, dt.month, dt.day,
                                 dt.hour, dt.minute, dt.second,
                                 0, tz)

#wc = WebCal('https://somewhere.com/dav/Calendar',
#            'name', 'password')

#ids = wc.getCalendarUIDs()
#print ids[2]
#c = wc.getCalendar(ids[2])

c = Calendar.from_string(open("test.ics","r").read())
ic = ICal(c)
print ic.getSummary()
ic.setSummary('blah')
print ic.getSummary()
print c.walk('VEVENT')[0].keys()
print c
dt =  ic.getStartDateTime()
print dt
ic.setStartDateTime(dt+datetime.timedelta(days=1))
print c

print ic.getDescription()
