import re
from datetime import datetime, timedelta

def totimestamp(s):
    if s is None or isinstance(s, int):
        return s
    ts = None
    if re.match('^\d\d:?\d\d:?\d\d$', s):
        s = ' '.join([str(datetime.now().date()), s])
    r = re.match('^(\d\d\d\d)-?(\d\d)-?(\d\d) ?(\d\d):?(\d\d):?(\d\d)$', s)
    if r:
        ts = int(datetime(
            int(r[1]), int(r[2]), int(r[3]),
            int(r[4]), int(r[5]), int(r[6])
        ).timestamp())

    return ts

