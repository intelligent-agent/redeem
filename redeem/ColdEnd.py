#!/usr/bin/env python
"""
This class represent a Dallas 1-wire teperature probe

Author: Elias Bakken
email: elias(dot)bakken(at)gmail(dot)com
Website: http://www.thing-printer.com
License: GNU GPL v3: http://www.gnu.org/copyleft/gpl.html

 Redeem is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 Redeem is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with Redeem.  If not, see <http://www.gnu.org/licenses/>.
"""

import logging
import glob

class ColdEnd: 
    def __init__(self, pin, name):
        """ Init """
        self.pin = pin
        self.name = name

    def get_temperature(self):	
        """ Return the temperature in degrees celsius """
        with open(self.pin, "r") as f:
            try:
                temperature = float(f.read().split("t=")[-1])/1000.0
            except IOError:
                logging.warning("Unable to get temperature from "+self.name)
                return -1            
        return temperature	
