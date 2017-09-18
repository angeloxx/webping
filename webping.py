#!/usr/bin/python
# Copyright (c) 1997-2017 Angelo Conforti
# 
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
# 
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# This script webping a page and alert if diffs. This script is compatible with Nagios/Icinga2
# and uses:
# pageres: npm install -g pageres-cli
# debian: apt install  python-skimage/stable nodejs/stretch pillow imagemagick
#
# Usage:
# webping.py --website www.angeloxx.it --area 0,0,1272,3357 --warning 10 --critical 30
# 

import os, sys, hashlib, subprocess, contextlib
from optparse import OptionParser
from PIL import Image


parser = OptionParser()
parser.add_option("--website", dest="website", help="The remote URL", default="www.angeloxx.it")
parser.add_option("--spooldir", dest="spooldir", help="The spool directory", default="/var/spool/webping")
parser.add_option("--area", dest="area", help="area in the topx,topy,bottomx,bottom-y", default="10,10,200,200")
parser.add_option("--verbose", dest="verbose", help="verbosity level", default=1)
parser.add_option("--reset", dest="reset", help="reset the web page", action="store_true", default=False)
parser.add_option("--warning", dest="warning", help="warning level", default=1)
parser.add_option("--critical", dest="critical", help="critical level", default=5)
parser.add_option("--baseweb", dest="baseweb", help="base web url of webping store", default="https://mon.angeloxx.lan/webping/")
(options, args) = parser.parse_args()

if not os.path.isdir(options.spooldir):
    print "UNKNOWN: Spool dir does not exist: %s" % (options.spooldir)
    sys.exit(3)


urlHash = hashlib.md5(options.website).hexdigest()

os.remove("%s/%s-cropped-new.jpg" % (options.spooldir,urlHash)) if os.path.exists("%s/%s-cropped-new.jpg" % (options.spooldir,urlHash)) else None
os.remove("%s/%s-site-new.jpg" % (options.spooldir,urlHash))  if os.path.exists("%s/%s-site-new.jpg" % (options.spooldir,urlHash)) else None


try:
    urlCaptured = subprocess.check_output(["/usr/bin/pageres",options.website,"1280x800","--format=jpg","--filename=%s-site-new" % (urlHash)], cwd=options.spooldir)
except subprocess.CalledProcessError as e:
    print "CRITICAL: Unable to capture %s" % (options.website)
    sys.exit(2)

imgOrig = Image.open("%s/%s-site-new.jpg" % (options.spooldir,urlHash))

area = options.area.split(",")
imgCropped = imgOrig.crop((int(area[0]), int(area[1]), int(area[2]), int(area[3])))
imgCropped.save("%s/%s-cropped-new.jpg" % (options.spooldir,urlHash))

if not os.path.isfile("%s/%s-cropped.jpg" % (options.spooldir,urlHash)) or options.reset:
    # Amen, primo giro
    print "OK: first screenshot taken"
    os.rename("%s/%s-cropped-new.jpg" % (options.spooldir,urlHash),"%s/%s-cropped.jpg" % (options.spooldir,urlHash))
    os.rename("%s/%s-site-new.jpg" % (options.spooldir,urlHash),"%s/%s-site.jpg" % (options.spooldir,urlHash))
    sys.exit(0)

imgOriginal = Image.open("%s/%s-cropped.jpg" % (options.spooldir,urlHash))
widthOriginal, heightOriginal = imgOriginal.size
widthCropped, heightCropped = imgCropped.size
if widthOriginal != widthCropped or heightOriginal != heightCropped:
    # Amen, cambiata crop size
    print "OK: updated screenshot taken"
    os.rename("%s/%s-cropped-new.jpg" % (options.spooldir,urlHash),"%s/%s-cropped.jpg" % (options.spooldir,urlHash))
    os.rename("%s/%s-site-new.jpg" % (options.spooldir,urlHash),"%s/%s-site.jpg" % (options.spooldir,urlHash))
    sys.exit(0)

# Accept the Exception
try:
    compared = subprocess.check_output(["/usr/bin/compare-im6.q16","-metric","RMSE","%s/%s-cropped.jpg" % (options.spooldir,urlHash),"%s/%s-cropped-new.jpg" % (options.spooldir,urlHash),"/tmp/diff.jpg"],stderr=subprocess.STDOUT)
    s = compared.split(" ")[0]
except subprocess.CalledProcessError as e:
    s = e.output.split(" ")[0]

try:
    value = float(s) if '.' in s or 'e' in s.lower() else int(s) 
except:
    print "UNKNOWN: %s" % compared
    sys.exit(3)
if value >= int(options.critical):
    print "CRITICAL: site %s differs for %dpct - see %s/%s-site-new.jpg" % (options.website,value,options.baseweb,urlHash)
    sys.exit(2)        
if value >= int(options.warning):
    print "WARNING: site %s differs for %dpct - see %s/%s-site-new.jpg" % (options.website,value,options.baseweb,urlHash)
    sys.exit(1)        
print "OK: site %s differs for %dpct - see %s/%s-site-new.jpg" % (options.website,value,options.baseweb,urlHash)
sys.exit(0)        
