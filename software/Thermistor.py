#!/usr/bin/env python
'''
A Stepper Motor Driver class for Replicape. 

Author: Elias Bakken
email: elias(dot)bakken(at)gmail(dot)com
Website: http://www.thing-printer.com
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
'''

import numpy as np
import logging
from threading import Lock

# Import the temp chart. 
from temp_chart import *

''' Represents a thermistor '''
class Thermistor: 
    mutex = Lock()

    def __init__(self, pin, name, chart_name):
        """ Init """
        self.pin = pin
        self.name = name
        self.temp_table = np.array(temp_chart[chart_name]).transpose()
	
    def getTemperature(self):	
        """ Return the temperature in degrees celcius """
        Thermistor.mutex.acquire()
        for i in xrange(10):           
            with open(self.pin, "r") as file:
                try:
                    voltage = (float(file.read().rstrip())/4096)*1.8
                    break
                except IOError as e:
                    logging.error("Unable to get ADC value for the {2}. time ({0}): {1}".format(e.errno, e.strerror, i))
                    voltage = 0                                                    
        Thermistor.mutex.release()
        res_val = self.voltage_to_resistance(voltage)     # Convert to resistance  
        temperature = self.resistance_to_degrees(res_val) # Convert to degrees
        #logging.debug(self.name+": voltage: %f"%(voltage))
        #logging.debug(" - thermistor res: %f - Temperature: %f deg."%(res_val, temperature))
        return temperature	
		
    def resistance_to_degrees(self, resistor_val):
	""" Return the temperature nearest to the resistor value """
        idx = (np.abs(self.temp_table[1]-resistor_val)).argmin()
        return self.temp_table[0][idx]

    def voltage_to_resistance(self, v_sense):
	""" Convert the voltage to a resistance value """
        if v_sense == 0:
            return 10000000.0
        return  4700.0/((1.8/v_sense)-1.0)
