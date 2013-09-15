''' 
This class represent a Dallas 1-wire teperature probe
'''

import logging

class W1: 

    def __init__(self, pin, name):
        ''' Init '''
        self.pin = pin
        self.name = name
        self.debug = 0

    def getTemperature(self):	
        ''' Return the temperature in degrees celcius '''
        with open(self.pin, "r") as f:
            try:
                temperature = float(f.read().split("t=")[-1])/1000.0
            except IOError:
                logging.warning("Unable to get temperature from "+self.name)
                return -1            
        return temperature	
		
    def setDebugLevel(self, val):
        ''' Set the deuglevel '''
        self.debug = val

