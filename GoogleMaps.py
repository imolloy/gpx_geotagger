import os
import os.path
import re

class GoogleMaps(object):
    exif_keys = ['EXIF ISOSpeedRatings', 'EXIF FocalLength', 'EXIF ExposureTime', 'EXIF FocalLengthIn35mmFilm', 'EXIF FNumber', 'EXIF Flash', 'EXIF ExposureBiasValue', 'EXIF ExposureProgram', 'EXIF ExposureMode']
    exif_map = {'EXIF ISOSpeedRatings' : 'ISO', 'EXIF FocalLength' : 'Focal', 'EXIF ExposureTime' : 'Shutter', 'EXIF FocalLengthIn35mmFilm' : '35mm Focal', 'EXIF FNumber' : 'F-Stop', 'EXIF Flash' : 'Flash', 'EXIF ExposureBiasValue' : 'Exposure Bias', 'EXIF ExposureProgram' : 'Exposure Program', 'EXIF ExposureMode' : 'Exposure Mode'}
    def __init__(self, map='~'):
        self.root = os.path.expanduser(map) + '/'
        os.makedirs(self.root + 'images')
        self.markers = []
        self.fd = open(self.root + 'index.html', 'w')
        
    def write_prefix(self, lat, lon):
        """Write a canned header to a full-window Google Maps Canvas"""
        # Open the Maps API and center at the mean of the data
        self.fd.write("""<!DOCTYPE html>
        <html>
        <head>
        <meta name="viewport" content="initial-scale=1.0, user-scalable=no" />
        <style type="text/css">
          html { height: 100%% }
          body { height: 100%%; margin: 0px; padding: 0px }
        </style>
        <script type="text/javascript"
            src="http://maps.google.com/maps/api/js?sensor=false">
        </script>
        <script type="text/javascript">
          function initialize() {
            var myLatlng = new google.maps.LatLng(%f, %f);
              var myOptions = {
                zoom: 14,
                center: myLatlng,
                mapTypeId: google.maps.MapTypeId.ROADMAP
              }
              var map = new google.maps.Map(document.getElementById("map_canvas"), myOptions);
              var infowindow = new google.maps.InfoWindow({
      content: 'No EXIF Data'
  });
              var contentStrings = {}
              """ % (lat, lon))
    def write_suffix(self):
        # Write a canned suffix to cloe remainng tags and initialize the canvas
        self.fd.write("""}
        </script>
        </head>
        <body onload="initialize()">
          <div id="map_canvas" style="width:100%; height:100%"></div>
        </body>
        </html>
        """)
        self.fd.close()
    def add_point(self, **kwargs):
        # Add the new marker
        self.markers.append(kwargs)
        # And write the embedded thumbnail to an images directory
        exif_thumb = open(self.root + 'images/' + self.thumb(kwargs['name']), 'wb')
        exif_thumb.write(kwargs['exif']['JPEGThumbnail'])
        exif_thumb.close()
    def make_content(self, **kwargs):
        # Make a little HTML Snippet that will display in Google Maps InfoWindow
        # Might as well present the EXIF Metadata in a table...
        res = '<table>'
        for k in  self.exif_keys:
            res += '<tr><td><b>%s</b></td><td>%s</td></tr>' % (self.exif_map[k], kwargs['exif'][k])
        res += '</table>'
        return res
    def thumb(self, name):
        # Correct the name of the thumbnail for the Google Maps InfoWindow
        return name[:name.rfind('.')] + '_tn.jpg'
    def URL(self):
        # Write some very ugly HTML to load Google Maps, and place one marker,
        # with a corresponding InfoWindow, at the location of each photo
        base_url = ''
        i = 0
        lats = []
        lons = []
        for d in self.markers:
            lats.append(d['lat'])
            lons.append(d['lon'])
            base_url += """var marker%d = new google.maps.Marker({
                      position: new google.maps.LatLng(%f, %f), 
                      map: map, 
                      title:"%s",
                      flat : true
                  });
                  """ % (i, d['lat'], d['lon'], d['name'])
            base_url += """contentStrings['%s'] = '<div id="content"><h2>%s</h2><img src="images/%s" style="float:left;margin:0 5px 0 0;"/>%s</div>';
            """ % (d['name'], d['name'], self.thumb(d['name']), self.make_content(**d))
            base_url += """google.maps.event.addListener(marker%d, 'click', function() {
              infowindow.content = contentStrings[marker%d.title]
              infowindow.open(map, marker%d);
            });
            
            """ % (i, i, i)
            i += 1
        self.write_prefix(sum(lats)/len(lats), sum(lons)/len(lons))
        self.fd.write(base_url)
        self.write_suffix()
