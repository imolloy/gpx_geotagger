"""
2011-06-03
Author Ian Molloy i.m.molloy@gmail.com
"""

from datetime import datetime

from xml.dom.minidom import parse, parseString

import iso8601

def parse_gpx_iter(f):
    """
    Hacky parser for GPX trackdata.
    It only tries to extract the trackpoints and segments, and makes no guarantees
    regarding the validity of the XML or GPX data.
    
    f : input stream to read
    """
    dom = parse (f)
    x = dom.getElementsByTagName('gpx')[0]
    for trk in x.getElementsByTagName('trk'):
        time = trk.getElementsByTagName('time')[0].firstChild.data
        for trkseg in trk.getElementsByTagName('trkseg'):
            points = trkseg.getElementsByTagName('trkpt')
            for point in points:
                t = point.getElementsByTagName('time')[0].firstChild.data
                ele = point.getElementsByTagName('ele')[0].firstChild.data
                lat = point.attributes['lat'].value
                lon = point.attributes['lon'].value
                # My GPX Files from Garmin are always given in Z-Time...
                tz = t.replace('Z','GMT')
                tm = datetime.strptime(tz,'%Y-%m-%dT%H:%M:%S%Z')
                yield (tm,lat,lon,ele)
