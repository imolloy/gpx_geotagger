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
