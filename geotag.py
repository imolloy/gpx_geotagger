import EXIF
from datetime import datetime,timedelta
import gps
import os,sys

# path_name = '/Volumes/NO NAME/DCIM/100MSDCF/DSC03064.ARW'
# gpx_file = '/Users/imolloy/Desktop/gpsbabel_output.gpx'

verbose = True
	
def nearest_time(points, t):
	if points[0][0] > t or points[-1][0] < t:
		if verbose:
			sys.stderr.write("Time not in range.\t%s %s %s\n" % (points[0][0], points[-1][0], t))
		return None
	a = 0
	b = len(points)-1
	while True:
		if a >= b:
			assert(a-b <= 1)
			return (points[b], points[a])
		m = (a+b)/2
		if verbose:
			sys.stderr.write('BSearch:\t A: %s(%d) M: %s(%d) B: %s(%d) T: %s\n' % (points[a][0], a, points[m][0], m, points[b][0], b, t))
		if points[m][0] == t:
			return (points[m], points[m])
		elif points[m][0] > t:
			b = m-1
			if points[b][0] < t:
				return (points[b], points[b+1])
		else:
			a = m+1
			if points[a][0] > t:
				return (points[a-1], points[a])

def interpolate(a, b, t):
	d1 = (t - a[0]).seconds
	d2 = (b[0] - t).seconds
	d = float(d1 + d2)
	point = []
	point.append(t)
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
	if verbose:
		sys.stderr.write('Interpolate:\t%s\t%s\t%s\n' % (a[0], t, b[0]))
	assert(a[0].toordinal() <= t.toordinal())
	assert(b[0].toordinal() >= t.toordinal())
	delta = b[0] - a[0]
	if delta.seconds > tolerance:
		# We could interpolate, but the error is too large
		return None
	if delta.seconds == 0:
		# No need to interpolate
		return a
	return interpolate(a, b, t)

def image_time(path_name, delta_hours=0, delta_minutes=0, delta_seconds=0):
	"""Opens an image, and returns the EXIF tags"""
	f = open(path_name, 'r')
	tags = EXIF.process_file(f)
	capture_time = tags['Image DateTime']
	img_time = capture_time.printable + 'GMT'
	cdt = datetime.strptime(img_time, '%Y:%m:%d %H:%M:%S%Z')
	delta = timedelta(hours=delta_hours, minutes=delta_minutes, seconds=delta_seconds)
	cdt = cdt - delta
	return cdt

if __name__ == '__main__':
	if len(sys.argv) < 2:
		sys.stderr.write("Usage: GPX_FILE ARW_FILES*\n")
		sys.exit(-1)
	gpx_file = sys.argv[1]
	points = gps.parse_gpx(gpx_file)
	
	for path_name in sys.argv[2:]:
		img_time = image_time(path_name, delta_minutes=55, delta_seconds=0)
		nearest = nearest_time(points, img_time)
		if nearest is None:
			sys.stderr.write('%s\n\tSkipping. Not in range. %s\n' % (path_name, img_time))
			continue
		point = interpolate_time(nearest[0], nearest[1], img_time)
		if point == None:
			sys.stderr.write('%s\n\tSkipping. Too much time between data points.\n' % path_name)
			continue
		if verbose:
			sys.stderr.write('%s\n\tCapture:\t%s\n\tMatch:\t\t%s\n\tLocation:\t%f %f %0.3f\n' % (path_name, img_time, point[0], float(point[1]), float(point[2]), float(point[3])))

		xmp_file = path_name.replace('ARW','XMP')
		cmd = 'exiftool "%s" -GPSLatitude=%f -GPSLatitudeRef=N -GPSLongitude=%f -GPSLongitudeRef=W -GPSAltitude=%f "%s"' % (path_name, float(point[1]), float(point[2]), float(point[3]), xmp_file)
		os.system(cmd)