#!/usr/bin/env python
"""
A temperature sensor class for Replicape.
This represents NTC and PTC sensors like thermistors, thermocouples
and PT100

The code borrows heavily from smoothieware which is available at:
https://github.com/Smoothieware/Smoothieware.
It was originally written by wolfmanjm


Author: Elias Bakken, Florian Hochstrasser
email: elias(dot)bakken(at)gmail(dot)com, thisis(at)parate(dot)ch
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

import numpy as np
import math
import logging
from threading import Lock
import sys

class TemperatureSensor:

	mutex = Lock()
	is_ntc = True 

	def __init__(self, pin, name, sensorIdentifier):
		""" Init """
		try:
        	self.sensorsThermistorSteinhart = exec(open("ThermistorSteinhartHartTables.py").read())
        except:
        	logging.error("no thermistor tables found")
        try:	
			self.sensorsPT100 = exec(open("PT100Tables.py"))
		except:
			logging.error("no tables for PT100 found")

		#Find matching entry in sensor tables and instantiate corresponding sensor
		found = False
		for s in self.sensorsThermistorSteinhart:
			if s[0] == self.sensorIdentifier:
				self.sensor = new Thermistor(pin, name, sensorIdentifier, s)
				found = True
				break

		if found == False:
			for s in self.sensorsPT100
				if s[0] == self.sensorIdentifier:
					self.sensor = new PT100((pin, name, sensorIdentifier, s)
					found = True
					break

		if found == False:
			logging.error("The specified temperature sensor "+sensorIdentifier+" is not implemented")
			sys.exit()


	def read_adc(self):

		maxAdc = 4095.0
    	mutex = Lock()
    	sig = -1.0

    	mutex.acquire()
    	try:
    		with open(self.pin, "r") as file:
    			sig = (float(file.read().rstrip())) / 4095.0 * 1.8
		except IOError as e:
			logging.error("Unable to get ADC value({0}: {1}".format(e.errno, e.strerror))
		finally:
			mutex.release()

		if(adc >= maxAdc or adc <= 0.0):
        	return -1.0
        else:
			return sig

	def get_temperature(self):
			self.sensor.get_temperature(resistance)



""" This class represents standard thermistor sensors.
	It borrows heavily from Smoothieware's code (https://github.com/Smoothieware/Smoothieware).
	wolfmanjm, thanks!
"""		
class Thermistor:

	def __init__(self, pin, name, sensorIdentifier, sensorConfiguration):
		""" Init """
        if len(sensorConfiguration) != 6:
        	logging.error("Sensor configuration is missing parameters. Should have 6, has "+len(sensorConfiguration))
        	sys.exit()
    	else
    		self.pin = pin
        	self.name = name
        	self.r1 = sensorConfiguration[1]
    		self.r2 = sensorConfiguration[2]
    		self.c1 = sensorConfiguration[3]
    		self.c2 = sensorConfiguration[4]
    		self.c3 = sensorConfiguration[5]

    
    def get_temperature(self):
        """ Return the temperature in degrees celsius. Uses Steinhart-Hart """
        maxAdc = 4095.0
        adc = read_adc()
        if(adc >= maxAdc or adc <= 0.0):
        	return -1.0

        r = float((self.r2 / (maxAdc / adc)) - 1.0)
        if(self.r1 > 0.0):
        	r = (r1 * r) / (r1 - r)
        l = float(math.log(r))

        t = float((1.0 / (self.c1 + self.c2 * l + self.c3 * math.pow(l,3))) - 273.15)

        return t


    def read_adc(self):

    	mutex = Lock()
    	ret = -1.0

    	mutex.acquire()
    	try:
    		with open(self.pin, "r") as file:
    			ret = (float(file.read().rstrip())) / 4095.0 * 1.8
		except IOError as e:
			logging.error("Unable to get ADC value({0}: {1}".format(e.errno, e.strerror))
		finally:
			mutex.release()
		
		if(adc >= maxAdc or adc <= 0.0):
        	return -1.0
        else:
			return ret


""" This class represents PT100 temperature sensors """
class PT100:

	def __init__(self, pin, name, sensorIdentifier, sensorConfiguration):

		if len(sensorConfiguration) != 4:
	        	logging.error("Sensor configuration is missing parameters. Should have 6, has "+len(sensorConfiguration))
	        	sys.exit()
    	else
    		self.pin = pin
        	self.name = name
        	self.r0 = sensorConfiguration[1]
    		self.a = sensorConfiguration[2]
    		self.b = sensorConfiguration[3]

    def get_temperature(self)
		maxAdc = 4095.0
        adc = read_adc()
        if(adc >= maxAdc or adc <= 0.0):
        	return -1.0

        #BIG questionmark: Is this right?
    	r = float(self.r0 / (maxAdc / adc)) - 1.0)

		"""
		For temperature > 0 °C, the formula is:
		t = (-r0*a + (r0^2*a^2 - 4*r0*b * (r0-r))^(1/2)) / 2*r0*b
		"""
		t = float(-self.r0*self.a
					+ math.sqrt(
						math.pow(self.r0,2)*math.pow(self.a,2)
						- 4*self.r0*self.b*(self.r0 - r))
					/ (2 * self.r0 * self.b))
		return t

    def read_adc(self):

    	mutex = Lock()
    	ret = -1.0

    	mutex.acquire()
    	try:
    		with open(self.pin, "r") as file:
    			ret = (float(file.read().rstrip())) / 4095.0 * 1.8
		except IOError as e:
			logging.error("Unable to get ADC value({0}: {1}".format(e.errno, e.strerror))
		finally:
			mutex.release()

		if(adc >= maxAdc or adc <= 0.0):
        	return -1.0
        else:
			return ret


class ThermoCouple:

