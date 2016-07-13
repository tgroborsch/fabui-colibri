#!/bin/env python
# -*- coding: utf-8; -*-
#
# (c) 2016 FABtotum, http://www.fabtotum.com
#
# This file is part of FABUI.
#
# FABUI is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# FABUI is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with FABUI.  If not, see <http://www.gnu.org/licenses/>.

# Import standard python module
import argparse
import time
import gettext
import os
import errno
from fractions import Fraction

# Import external modules
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
from picamera import PiCamera

# Import internal modules
from fabtotum.fabui.config  import ConfigService
from fabtotum.fabui.gpusher import GCodePusher

def makedirs(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

config = ConfigService()

# SETTING EXPECTED ARGUMENTS
parser = argparse.ArgumentParser(add_help=False, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("-d", "--dest",     help="Destination folder.",     default=config.get('general', 'bigtemp_path') )
parser.add_argument("-s", "--slices",   help="Number of slices.",       default=100)
parser.add_argument("-i", "--iso",      help="ISO.",                    default=400)
parser.add_argument("-p", "--power",    help="Scan laser power 0-255.", default=230)
parser.add_argument("-w", "--width",    help="Image width in pixels.",  default=1920)
parser.add_argument("-h", "--height",   help="Image height in pixels",  default=1080)
parser.add_argument("-b", "--begin",    help="Begin scanning from X.",  default=0)
parser.add_argument("-e", "--end",      help="End scanning at X.",      default=360)
parser.add_argument("-z", "--z-offset", help="Z offset.",               default=0)
parser.add_argument("-y", "--y-offset", help="Y offset.",               default=0)
parser.add_argument("-a", "--a-offset", help="A offset/rotation.",      default=0)
parser.add_argument('--help', action='help', help='show this help message and exit')

# GET ARGUMENTS
args = parser.parse_args()

slices          = args.slices
destination     = args.dest
iso             = args.iso
power           = args.power
start_a         = args.begin
end_a           = args.end
width           = args.width
height          = args.height
z_offset        = args.z_offset
y_offset        = args.y_offset
a_offset        = args.a_offset

monitor_file    = config.get('general', 'task_monitor')      # TASK MONITOR FILE (write stats & task info, es: temperatures, speed, etc
log_trace       = config.get('general', 'trace')        # TASK TRACE FILE 

scan_dir        = os.path.join(destination, "images")

if not os.path.exists(scan_dir):
    makedirs(scan_dir)

################################################################################

print 'ROTARY SCAN MODULE STARTING' 
print 'scanning from'+str(start_a)+"to"+str(end_a); 
print 'Num of scans : ', slices
print 'ISO  setting : ', iso
print 'Resolution   : ', width ,'*', height, ' px'
print 'Laser PWM.  : ', power
print 'z offset     : ', z_offset

#ESTIMATED SCAN TIME ESTIMATION
estimated=(slices*1.99)/60
if(estimated<1):
    estimated*=60
    unit= "Seconds"
else:
    unit= "Minutes"

print 'Estimated Scan time =', str(estimated) + " " + str(unit) + "  [Pessimistic]"

#ESTIMATED SCAN TIME ESTIMATION
estimated = (slices*1.99)/60
if estimated<1 :
    estimated *= 60
    unit= "Seconds"
else:
    unit= "Minutes"

print 'Estimated Scan time =', str(estimated) + " " + str(unit) + "  [Pessimistic]"

################################################################################

class RotaryScan(GCodePusher):
    def __init__(self, log_trace, monitor_file, scan_dir, width = 2592, height = 1944, rotation = 270, iso = 800, power = 230, shutter_speed = 35000):
        super(RotaryScan, self).__init__(log_trace, monitor_file)
        
        self.camera = PiCamera()
        self.camera.resolution = (width, height)
        self.camera.iso = iso
        self.camera.awb_mode = 'off'
        self.camera.awb_gains = ( Fraction(1.5), Fraction(1.2) )
        self.camera.rotation = rotation
        self.camera.shutter_speed = shutter_speed # shutter_speed in microseconds
        
        self.progress = 0.0
        self.laser_power = power
        self.scan_dir = scan_dir
            
    def get_progress(self):
        """ Custom progress implementation """
        return self.progress
    
    def take_a_picture(self, number = 0, suffix = ''):
        """ Camera control wrapper """
        scanfile = os.path.join(self.scan_dir, "{0}{1}.jpg".format(number, suffix) )
        self.camera.capture(scanfile, quality=100)
    
    def run(self, start_a, end_a, y_offset, slices):
        self.exec_macro("start_rotary_scan")
        
        LASER_ON  = 'M700 S{0}'.format(self.laser_power)
        LASER_OFF = 'M700 S0'
        
        position = start_a
        
        if start_a != 0:
            # If an offset is set .
            self.send('G0 E{0} F800'.format(start_a) )
            
        if(y_offset!=0):
            #if an offset for Z (Y in the rotated reference space) is set, moves to it.
            self.send('G0 Y{0}'.format(y_offset))  #go to y offset

        self.send('M701 S0')
        self.send('M702 S0')
        self.send('M703 S0')
        
        #~ dx = abs((float(end_x)-float(start_x))/float(slices))  #mm to move each slice
        deg = abs((float(end_a)-float(start_a))/float(slices))  #degrees to move each slice
        
        for i in xrange(0, slices):
            #move the laser!
            print str(i) + "/" + str(slices) +" (" + str(deg*i) + "/" + str(deg*slices) +")"
            
            self.send('G0 E{0} F800'.format(position))
            self.send('M400')

            self.send(LASER_ON)
            self.take_a_picture(i, '_l')
            
            self.send(LASER_OFF)
            self.take_a_picture(i)
            
            position += deg
            
            self.progress = (i+1) / slices
        
        self.exec_macro("end_scan")
        
        self.stop()
                
app = RotaryScan(log_trace, 
                monitor_file,
                scan_dir,
                width=width,
                height=height,
                iso=iso,
                power=power)

app.run(start_a, end_a, y_offset, slices)
app.loop()
