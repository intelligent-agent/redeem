#!/usr/bin/env python
''' 
This class represent a Dallas 1-wire teperature probe

Author: Elias Bakken
email: elias(dot)bakken(at)gmail(dot)com
Website: http://www.thing-printer.com
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
'''

import logging

class W1: 
    def __init__(self, pin, name):
        ''' Init '''
        self.pin = pin
        self.name = name

    def getTemperature(self):	
        ''' Return the temperature in degrees celcius '''
        with open(self.pin, "r") as f:
            try:
                temperature = float(f.read().split("t=")[-1])/1000.0
            except IOError:
                logging.warning("Unable to get temperature from "+self.name)
                return -1            
        return temperature	
