"""
2011-06-03
Author Ian Molloy i.m.molloy@gmail.com
"""

# Copyright (c) 2011 Ian Molloy All rights reserved
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  1. Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#
#  2. Redistributions in binary form must reproduce the above
#     copyright notice, this list of conditions and the following
#     disclaimer in the documentation and/or other materials provided
#     with the distribution.
#
#  3. Neither the name of the authors nor the names of its contributors
#     may be used to endorse or promote products derived from this
#     software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import sys
import os
import os.path
from datetime import datetime,timedelta
from optparse import OptionParser

import sqlite3
import progressbar
import EXIF

import gps
from GoogleMaps import GoogleMaps

class GeoTagImage(object):
    """GeoTagImage Class"""
    def __init__(self, **kwargs):
        self.gpx_file = kwargs['gpx_file']
        self.verbose = kwargs['verbose']
        self.xmp = kwargs['xmp']
        self.hours = kwargs['hours']
        self.minutes = kwargs['minutes']
        self.seconds = kwargs['seconds']
        self.execute = kwargs['execute']
        self.process_timestamps()
        self.files_read = 0
        self.files_tagged = 0
        self.GM = GoogleMaps()
    
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
        if len(tags) == 0 or 'Image DateTime' not in tags:
            return None
        capture_time = tags['Image DateTime']
        # Add the timezone the camera time is set to
        img_time = capture_time.printable + timezone
        # Parse the timestap
        cdt = datetime.strptime(img_time, '%Y:%m:%d %H:%M:%S%Z')
        # And process the offset for clock skew
        delta = timedelta(hours=delta_hours, minutes=delta_minutes, seconds=delta_seconds)
        cdt = cdt - delta
        self.files_read += 1
        return cdt
    
    def correlate_timestamp(self, *args):
        if os.isatty(1):
            pbar = progressbar.ProgressBar(len(args), widgets=[progressbar.ETA(), ' ', progressbar.Percentage(), ' ', progressbar.Bar()]).start()
        for i,path_name in enumerate(args):
            if os.isatty(1):
                pbar.update(i)
            img_time = self.image_time(path_name, delta_hours=self.hours, delta_minutes=self.minutes, delta_seconds=self.seconds)
            if img_time is None:
                if self.verbose:
                    sys.stderr.write('%s\n\tNo Time...Not an image?\n' % path_name)
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
            if self.xmp:
                xmp_file = '"%s.XMP"' % path_name[:path_name.rfind('.')]
            else: xmp_file = ''
            cmd = 'exiftool "%s" -GPSLatitude=%f -GPSLatitudeRef=N -GPSLongitude=%f -GPSLongitudeRef=W -GPSAltitude=%f %s > /dev/null' % (path_name, float(point[1]), float(point[2]), float(point[3]), xmp_file)
            self.GM.add_point(lat=point[1], lon=point[2], name=os.path.split(path_name)[1], time=img_time, exif=EXIF.process_file(open(path_name, 'r')))
            if self.execute:
                retval = os.system(cmd)
                if retval != 0:
                    sys.stderr.write("Error Processing Last Command:\n\t%s\n" % cmd)
                else:
                    self.files_tagged += 1
        if os.isatty(1):
            pbar.finish()
    

def main(*args, **options):
    gti = GeoTagImage(**options)
    if options['input'] != None:
        fp = options['input']
        if os.path.isdir(fp):
            gti.correlate_timestamp(*map(lambda x: '%s/%s' % (fp,x), os.listdir(fp)))
    else:
        gti.correlate_timestamp(*args)
    sys.stdout.write('%d Timestamped Photos\n%d Successfully GeoTagged Photos\n' % (gti.files_read, gti.files_tagged))
    gti.GM.URL()

if __name__ == '__main__':
    parser = OptionParser()
    # Input and Output
    parser.add_option('--gpx', dest='gpx_file', default=None, help='GPX Trackpoint File')
    parser.add_option('-i', '--input', dest='input', default=None, help='Input Directory')
    parser.add_option('-x', '--XMP', dest='xmp', default=False, action='store_true', help='Output XML File')
    parser.add_option('-e', '--exe', dest='execute', default=False, action='store_true', help='Execute and Tag the files. Dry-run otherwise')
    # Time Offsets
    parser.add_option('--hours', dest='hours', default=0, type='int', help='Time Offset in Hours')
    parser.add_option('--minutes', dest='minutes', default=0, type='int', help='Time Offset in Minutes')
    parser.add_option('--seconds', dest='seconds', default=0, type='int', help='Time Offset in Seconds')
    # Other Options
    parser.add_option('-v', '--verbose', dest='verbose', default=False, action='store_true', help='Verbose Output')
    (options, args) = parser.parse_args()
    main(*args, **options.__dict__)
    