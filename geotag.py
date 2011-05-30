import EXIF
from datetime import datetime,timedelta
import gps
import os,sys
import sqlite3
import progressbar

verbose = False

def nearest_time_sql(cursor, t):
    """
    Uses the Database to search for the nearest two points
    """
    if verbose:
        print 'SQL Time',t
    cursor.execute('SELECT * FROM tracklog WHERE dt <= ? ORDER BY dt DESC LIMIT 1', (t,))
    d = cursor.fetchone()
    if d != None:
        t0 = [datetime.strptime(d[0],'%Y-%m-%d %H:%M:%S')]
        t0.extend(d[1:])
    else:
        t0 = None
    cursor.fetchall()
    cursor.execute('SELECT * FROM tracklog WHERE dt >= ? ORDER BY dt LIMIT 1', (t,))
    d2 = cursor.fetchone()
    if d2 != None:
        t1 = [datetime.strptime(d2[0],'%Y-%m-%d %H:%M:%S')]
        t1.extend(d2[1:])
    else:
        t1 = None
    cursor.fetchall()
    if verbose:
        print 'SQL Resuls',t0,t1
    if t0 == None or t1 == None:
        return None
    return t0,t1

def interpolate(a, b, t):
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
    if verbose:
        sys.stderr.write('Interpolate:\n')
        sys.stderr.write('\t%s\n' % repr(a))
        sys.stderr.write('\t%s\n' % repr(point))
        sys.stderr.write('\t%s\n' % repr(b))
    return point

def interpolate_time(a, b, t, tolerance=100):
    """
    Calcultes the difference between two timestamps.
    If the difference is greater than a threshold, returns None
    Otherwise, interpolates the GPS Coordinates between the two points.
    """
    if verbose:
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
    return interpolate(a, b, t)

def image_time(path_name, timezone='GMT', delta_hours=0, delta_minutes=0, delta_seconds=0):
    """
    Opens an image, and returns the timestamp from the EXIF tags
    offset by delta_hours, delta_minutes, and delta_seconds
    """
    # Open the file for reading
    f = open(path_name, 'r')
    # And extract the tags
    tags = EXIF.process_file(f)
    capture_time = tags['Image DateTime']
    # Add the timezone the camera time is set to
    img_time = capture_time.printable + timezone
    # Parse the timestap
    cdt = datetime.strptime(img_time, '%Y:%m:%d %H:%M:%S%Z')
    # And process the offset for clock skew
    delta = timedelta(hours=delta_hours, minutes=delta_minutes, seconds=delta_seconds)
    cdt = cdt - delta
    return cdt

def correlate_timestamp(*args):
    pbar = progressbar.ProgressBar(len(args), widgets=[progressbar.ETA(), ' ', progressbar.Percentage(), ' ', progressbar.Bar()]).start()
    for i,path_name in enumerate(args):
        pbar.update(i)
        img_time = image_time(path_name, delta_minutes=55, delta_seconds=0)
        nearest = nearest_time_sql(cursor, img_time)
        if nearest is None:
            if verbose:
                sys.stderr.write('%s\n\tSkipping. Not in range. %s\n' % (path_name, img_time))
            continue
        point = interpolate_time(nearest[0], nearest[1], img_time)
        if point == None:
            if verbose:
                sys.stderr.write('%s\n\tSkipping. Too much time between data points.\n' % path_name)
            continue
        if verbose:
            sys.stderr.write('%s\n\tCapture:\t%s\n\tMatch:\t\t%s\n\tLocation:\t%f %f %0.3f\n' % (path_name, img_time, point[0], float(point[1]), float(point[2]), float(point[3])))
        xmp_file = path_name.replace('ARW','XMP')
        cmd = 'exiftool "%s" -GPSLatitude=%f -GPSLatitudeRef=N -GPSLongitude=%f -GPSLongitudeRef=W -GPSAltitude=%f "%s" > /dev/null' % (path_name, float(point[1]), float(point[2]), float(point[3]), xmp_file)
        retval = os.system(cmd)
        if retval != 0:
            sys.stderr.write("Error Processing Last Command:\n\t%s\n" % cmd)
    pbar.finish()

def process_timestamps(gpx_file):
    """
    Inserts the timestamps from the GPX file into an SQLite DB
    Returns a cursor to the DB
    """
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE tracklog(dt PRIMARY KEY, lat REAL, lon REAL, elev REAL)')
    for d in gps.parse_gpx_iter(gpx_file):
        cursor.execute('INSERT INTO tracklog VALUES(?,?,?,?)', d)
    conn.commit()
    return cursor

if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.stderr.write("Usage: GPX_FILE ARW_FILES*\n")
        sys.exit(-1)
    gpx_file = sys.argv[1]
    cursor = process_timestamps(gpx_file)
    correlate_timestamp(*sys.argv[2:])
