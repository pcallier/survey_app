#!/usr/bin/env python
"""date_stuff.py"""

import datetime

def do_dst(date):
	dst_offset=1
	dst_times = [(datetime.datetime(year=2014,month=3,day=9),datetime.datetime(year=2014,month=11,day=2)),
	(datetime.datetime(year=2015,month=3,day=8),datetime.datetime(year=2015,month=11,day=1)),
	(datetime.datetime(year=2016,month=3,day=13),datetime.datetime(year=2016,month=11,day=6)),
	(datetime.datetime(year=2017,month=3,day=12),datetime.datetime(year=2017,month=11,day=5))]
	if any([start < date < end for start, end in dst_times]):
		return date + datetime.timedelta(hours=dst_offset)
	else:
		return date

utc_offset=datetime.timedelta(hours=-8)

