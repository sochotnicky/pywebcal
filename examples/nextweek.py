#================== CONFIG ================
url = 'CALENDAR URL'
username = 'YOUR LOGIN'
passwd = 'YOUR PASSWORD'

#================ END CONFIG ==============

from pywebcal import WebCal, ICal
from datetime import datetime, timedelta
from dateutil.tz import tzical, gettz

wc = WebCal(url, username, passwd)
uids = wc.get_calendar_uids()

n = datetime.now(gettz())
u = n + timedelta(days=7)

events = []
for uid in uids:
    cal = wc.get_calendar(uid)

    es = cal.events_between(n, u)
    for dt, e in es:
        events.append(e)

for e in sorted(events, key=lambda event:event.get_start_datetime()):
    print "%s: %s" % (e.get_start_datetime(),
            e.get_summary().encode('utf-8'))
