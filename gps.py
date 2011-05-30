from xml.dom.minidom import parse, parseString
import iso8601
from datetime import datetime

def parse_gpx_iter(f):
    dom = parse (f)
    results = []
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
                # My GPX Files from Garmin are always gizen in Z-Time...
                tz = t.replace('Z','GMT')
                tm = datetime.strptime(tz,'%Y-%m-%dT%H:%M:%S%Z')
                yield (tm,lat,lon,ele)
