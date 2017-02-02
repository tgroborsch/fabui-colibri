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

from StringIO import StringIO as BytesIO
import pycurl, json, os
from fabtotum.fabui.config  import ConfigService

class RemoteVersion:
    
    def __init__(self, arch='armhf', mcu='atmega1280', config=None):
        self.config = config
        if not config:
            self.config = ConfigService()
        
        self.colibri_endpoint = self.config.get('updates', 'colibri_endpoint')
        self.firmware_endpoint = self.config.get('updates', 'firmware_endpoint')
        self.arch = arch
        self.mcu = mcu
        self.colibri = None
        self.firmware = None
        self.setColibri()
        self.setFirmware()
    
    def getRemoteData(self, endpoint):
        curl = pycurl.Curl()
        buffer = BytesIO()
        curl.setopt(pycurl.URL, endpoint)
        curl.setopt(pycurl.TIMEOUT, 10)
        curl.setopt(pycurl.FOLLOWLOCATION, 1)
        curl.setopt(pycurl.MAXREDIRS, 5)
        curl.setopt(curl.WRITEDATA, buffer)
        curl.perform()
        
        return buffer.getvalue()
        
    def setColibri(self):
        self.colibri = json.loads(self.getRemoteData("{0}/{1}/version.json".format(self.colibri_endpoint, self.arch)))
        
    def setFirmware(self):
        self.firmware = json.loads(self.getRemoteData("{0}/fablin/{1}/version.json".format(self.firmware_endpoint, self.mcu)))
    
    def getColibri(self):
        return self.colibri
    
    def getBundles(self):
        return self.colibri['bundles']
        
    def getBoot(self):
        return self.colibri['boot']
        
    def getImages(self):
        return self.colibri['images']
    
    def getFirmware(self):
        if 'firmware' in self.firmware:
            return self.firmware['firmware']
        return {}
    
    def getColibriEndpoint(self):
        return os.path.join(self.colibri_endpoint, self.arch)
        
    def getFirmwareEndpoint(self):
        return os.path.join(self.firmware_endpoint, 'fablin', self.mcu)
        
        
