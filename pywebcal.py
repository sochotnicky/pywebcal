import sys

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
        for event in self.ical.walk('VEVENT'):
            return vDatetime.from_ical(str(event['DTSTART']))

    def setStartDateTime(self, dt):
        for event in self.ical.walk('VEVENT'):
            vdt = vDatetime(dt)
            event['DTSTART'] = vdt.ical()

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
ic.setStartDateTime(dt+datetime.timedelta(days=1))
print c
