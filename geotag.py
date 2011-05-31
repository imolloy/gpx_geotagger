import sys
import os
import os.path
from datetime import datetime,timedelta
from optparse import OptionParser

import sqlite3
import progressbar
import EXIF

import gps

verbose = False

class GeoTagImage(object):
    """GeoTagImage Class"""
    def __init__(self, **kwargs):
        self.gpx_file = kwargs['gpx_file']
        self.verbose = kwargs['verbose']
        self.process_timestamps()
    
    def process_timestamps(self):
        """
        Inserts the timestamps from the GPX file into an SQLite DB
        Returns a cursor to the DB
        """
        self.conn = sqlite3.connect(':memory:')
        self.cursor = self.conn.cursor()
        self.cursor.execute('CREATE TABLE tracklog(dt PRIMARY KEY, lat REAL, lon REAL, elev REAL)')
        for d in gps.parse_gpx_iter(self.gpx_file):
            self.cursor.execute('INSERT INTO tracklog VALUES(?,?,?,?)', d)
        self.conn.commit()

    def nearest_time_sql(self, t):
        """
        Uses the Database to search for the nearest two points
        """
        if self.verbose:
            print 'SQL Time',t
        self.cursor.execute('SELECT * FROM tracklog WHERE dt <= ? ORDER BY dt DESC LIMIT 1', (t,))
        d = self.cursor.fetchone()
        if d != None:
            t0 = [datetime.strptime(d[0],'%Y-%m-%d %H:%M:%S')]
            t0.extend(d[1:])
        else:
            t0 = None
        self.cursor.fetchall()
        self.cursor.execute('SELECT * FROM tracklog WHERE dt >= ? ORDER BY dt LIMIT 1', (t,))
        d2 = self.cursor.fetchone()
        if d2 != None:
            t1 = [datetime.strptime(d2[0],'%Y-%m-%d %H:%M:%S')]
            t1.extend(d2[1:])
        else:
            t1 = None
        self.cursor.fetchall()
        if self.verbose:
            print 'SQL Resuls',t0,t1
        if t0 == None or t1 == None:
            return None
        return t0,t1

    def interpolate(self, a, b, t):
        """
        Does the actual interpolation work between two points
        """
        d1 = (t - a[0]).seconds
        d2 = (b[0] - t).seconds
        # The total time difference
        d = float(d1 + d2)
        point = []
        # Need to return a (time, lat, lon, elev) point
        point.append(t)
        # Linear interpolation of the latitude, longitude, and elevation
        point.append(float(a[1])*(d2/d) + float(b[1])*(d1/d))
        point.append(float(a[2])*(d2/d) + float(b[2])*(d1/d))
        point.append(float(a[3])*(d2/d) + float(b[3])*(d1/d))
        if self.verbose:
            sys.stderr.write('Interpolate:\n')
            sys.stderr.write('\t%s\n' % repr(a))
            sys.stderr.write('\t%s\n' % repr(point))
            sys.stderr.write('\t%s\n' % repr(b))
        return point

    def interpolate_time(self, a, b, t, tolerance=100):
        """
        Calcultes the difference between two timestamps.
        If the difference is greater than a threshold, returns None
        Otherwise, interpolates the GPS Coordinates between the two points.
        """
        if self.verbose:
            sys.stderr.write('Interpolate:\t%s\t%s\t%s\n' % (a[0], t, b[0]))
        # First, ensure the timestamps are in fact correctly formatted
        assert(a[0].toordinal() <= t.toordinal())
        assert(b[0].toordinal() >= t.toordinal())
        # The difference in time between the two points
        delta = b[0] - a[0]
        if delta.seconds > tolerance:
            # We could interpolate, but the error is too large
            return None
        if delta.seconds == 0:
            # No need to interpolate
            return a
        # Otherwise, we need to interpolate the time
        return self.interpolate(a, b, t)

    def image_time(self, path_name, timezone='GMT', delta_hours=0, delta_minutes=0, delta_seconds=0):
        """
        Opens an image, and returns the timestamp from the EXIF tags
        offset by delta_hours, delta_minutes, and delta_seconds
        """
        # Open the file for reading
        f = open(path_name, 'r')
        # And extract the tags
        tags = EXIF.process_file(f)
        f.close()
        if len(tags) == 0:
            return None
        capture_time = tags['Image DateTime']
        # Add the timezone the camera time is set to
        img_time = capture_time.printable + timezone
        # Parse the timestap
        cdt = datetime.strptime(img_time, '%Y:%m:%d %H:%M:%S%Z')
        # And process the offset for clock skew
        delta = timedelta(hours=delta_hours, minutes=delta_minutes, seconds=delta_seconds)
        cdt = cdt - delta
        return cdt

    def correlate_timestamp(self, *args):
        pbar = progressbar.ProgressBar(len(args), widgets=[progressbar.ETA(), ' ', progressbar.Percentage(), ' ', progressbar.Bar()]).start()
        for i,path_name in enumerate(args):
            pbar.update(i)
            img_time = self.image_time(path_name, delta_minutes=55, delta_seconds=0)
            if img_time is None:
                if self.verbose:
                    sys.stderr.write('%s\n\tNo Time...Not an image? %s\n' % path_name)
                continue
            nearest = self.nearest_time_sql(img_time)
            if nearest is None:
                if self.verbose:
                    sys.stderr.write('%s\n\tSkipping. Not in range. %s\n' % (path_name, img_time))
                continue
            point = self.interpolate_time(nearest[0], nearest[1], img_time)
            if point == None:
                if self.verbose:
                    sys.stderr.write('%s\n\tSkipping. Too much time between data points.\n' % path_name)
                continue
            if self.verbose:
                sys.stderr.write('%s\n\tCapture:\t%s\n\tMatch:\t\t%s\n\tLocation:\t%f %f %0.3f\n' % (path_name, img_time, point[0], float(point[1]), float(point[2]), float(point[3])))
            xmp_file = path_name.replace('ARW','XMP')
            cmd = 'exiftool "%s" -GPSLatitude=%f -GPSLatitudeRef=N -GPSLongitude=%f -GPSLongitudeRef=W -GPSAltitude=%f "%s" > /dev/null' % (path_name, float(point[1]), float(point[2]), float(point[3]), xmp_file)
            retval = os.system(cmd)
            if retval != 0:
                sys.stderr.write("Error Processing Last Command:\n\t%s\n" % cmd)
        pbar.finish()

def main(*args, **options):
    gti = GeoTagImage(**options)
    if options['input'] != None:
        fp = options['input']
        if os.path.isdir(fp):
            gti.correlate_timestamp(*map(lambda x: '%s/%s' % (fp,x), os.listdir(fp)))
    else:
        gti.correlate_timestamp(*args)

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option('--gpx', dest='gpx_file', default=None, help='GPX Trackpoint File')
    parser.add_option('-i', '--input', dest='input', default=None, help='Input Directory')
    parser.add_option('-v', '--verbose', dest='verbose', default=False, action='store_true', help='Verbose Output')
    (options, args) = parser.parse_args()
    print options,args
    main(*args, **options.__dict__)
    