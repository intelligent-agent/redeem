#!/usr/bin/env python
"""
A temperature chart class for Replicape.

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

import glob
import logging
import os

class Chart:
    
    charts ={}
    
    def __init__(self):
        """
        initialize a chart instance
        """
        
        # do nothing...
        
        return
    
    def load(self, file_location="etc/redeem/"):
        """
        provide a location to load temperature charts from
        and then load the charts
        """

        # get a list 
        files = glob.glob(os.path.join(file_location,"*.cht"))

        if not files:
            logging.warning("no temperature charts found in " + file_location)
        else:
            # load all temperature charts
            temp_chart = {}
            for f in files:
                execfile(f)
            self.charts = temp_chart
    
    def get(self, name):
        """
        return a named chart
        """
        
        return self.charts[name]
        

# define a global instance
temperature_charts = Chart()