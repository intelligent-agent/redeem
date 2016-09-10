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
import TemperatureSensorConfigs
from Alarm import Alarm

class TemperatureSensor:

    mutex = Lock()

    def __init__(self, pin, heater_name, sensorIdentifier):

        self.pin = pin
        self.heater = heater_name
        self.sensorIdentifier = sensorIdentifier
        self.maxAdc = 4095.0

        #Find matching entry in sensor tables and instantiate corresponding sensor
        found = False
        for s in TemperatureSensorConfigs.thermistors_shh:
            if s[0] == self.sensorIdentifier:
                self.sensor = Thermistor(pin, s, self.heater)
                found = True
                break

        if found == False:
            for p in TemperatureSensorConfigs.pt100:
                if p[0] == self.sensorIdentifier:
                    logging.warning("PT100 temperature sensor support is experimental at this stage.")
                    """ Experimental solution """
                    self.sensor = PT100(pin, p, self.heater)
                    found = True
                    break

        if found == False:
            for p in TemperatureSensorConfigs.tboard:
                if p[0] == self.sensorIdentifier:
                    logging.warning("Tboard sensors are experimental")
                    """ Not working yet. No known hardware solution """
                    self.sensor = Tboard(pin, p, self.heater)
                    found = True
                    break

        if found == False:
            logging.error("The specified temperature sensor {0} is not implemented. \
            You may add it's config in TemperatureSensorConfigs.".format(sensorIdentifier))
            self.sensor = None

    """
    Returns the current temperature in degrees celsius for the given sensor.
    """
    def get_temperature(self):
        voltage = self.read_adc()
        if not self.sensor:
            return 0.0
        return self.sensor.get_temperature(voltage)


    """
    Reads the adc pin and returns the actual voltage value
    Returns -1 if the reading is out of range.
    """
    def read_adc(self):
        voltage = 0

        TemperatureSensor.mutex.acquire()
        try:
            with open(self.pin, "r") as file:
                signal = float(file.read().rstrip())
                if(signal > self.maxAdc or signal <= 0.0):
                    voltage = -1.0
                else:
                    voltage = signal / self.maxAdc * 1.8 #input range is 0 ... 1.8V
        except IOError as e:
             Alarm(Alarm.THERMISTOR_ERROR, "Unable to get ADC value ({0}): {1}".format(e.errno, e.strerror))

        TemperatureSensor.mutex.release()
        return voltage


""" This class represents standard thermistor sensors.
    It borrows heavily from Smoothieware's code (https://github.com/Smoothieware/Smoothieware).
    wolfmanjm, thanks!
"""
class Thermistor(TemperatureSensor):

    def __init__(self, pin, sensorConfiguration, name):
        """ Init """
        self.name = name
        if len(sensorConfiguration) != 5:
            Alarm(Alarm.THERMISTOR_ERROR, "Sensor configuration for {0} is missing parameters. Expected: 5, received: {1}.".format(pin, len(sensorConfiguration)))
        else:
            self.pin = pin
            self.sensorIdentifier = sensorConfiguration[0] # The identifier
            self.r1 = sensorConfiguration[1]    #pullup resistance
            self.c1 = sensorConfiguration[2]    #Steinhart-Hart coefficient
            self.c2 = sensorConfiguration[3]    #Steinhart-Hart coefficient
            self.c3 = sensorConfiguration[4]    #Steinhart-Hart coefficient
            logging.debug("Initialized temperature sensor at {0} (type: {1}). Pullup value = {2} Ohm. Steinhart-Hart coefficients: c1 = {3}, c2 = {4}, c3 = {5}.".format(pin, sensorConfiguration[0], sensorConfiguration[1], sensorConfiguration[2], sensorConfiguration[3],sensorConfiguration[4]))



    def get_temperature(self, voltage):
        """ Return the temperature in degrees celsius. Uses Steinhart-Hart """
        r = self.voltage_to_resistance(voltage)
        #if self.name == "MOSFET E":
        #    logging.debug("Voltage: "+str(voltage))
        #    logging.debug("resistance: "+str(r))
        if r > 0:
            l = math.log(r)
            t = float((1.0 / (self.c1 + self.c2 * l + self.c3 * math.pow(l,3))) - 273.15)
        else:
            t = -273.15
            logging.debug("Reading sensor {0} on {1}, but it seems to be out of bounds. R is {2}. Setting temp to {3}.".format(self.sensorIdentifier, self.pin,r,t))
        return max(t, 0.0) # Cap it at 0

    def voltage_to_resistance(self,voltage):
        """ Convert the voltage to a resistance value """
        if voltage == 0 or (abs(voltage - 1.8) < 0.0001):
            return 10000000.0
        return self.r1 / ((1.8 / voltage) - 1.0)


"""
This class represents PT100 temperature sensors
Caution: This code is experimental.

"""
class PT100(TemperatureSensor):

    def __init__(self, pin, sensorConfiguration, name):

        if len(sensorConfiguration) != 5:
            logging.error("PT100 Sensor configuration for {0} is missing parameters. Expected: 5, received: {1}.".format(pin, len(sensorConfiguration)))    
            Alarm(Alarm.THERMISTOR_ERROR, "PT100 Sensor configuration for {0} is missing parameters. Expected: 5, received: {1}.".format(pin, len(sensorConfiguration)))
        else:
            self.pin = pin
            self.name = name
            self.sensorIdentifier = sensorConfiguration[0] # The identifier
            self.pullup = sensorConfiguration[1]
            self.R0 = sensorConfiguration[2]
            self.A  = sensorConfiguration[3]
            self.B  = sensorConfiguration[4]

    # The following calculations are based on the PT100 connected in the same as as a thermistor.
    # Connecting it this way will give very low accuracy, but better accuracy require hardware modification.
    def voltage_to_resistance(self,voltage):

        """ Convert the voltage to a resistance value """
        if voltage == 0 or (abs(voltage - 1.8) < 0.0001):
            return 10000000.0
        return self.pullup / ((1.8 / voltage) - 1.0)


    def get_temperature(self, voltage):
        """ Return the temperature in degrees celsius. """
        r = self.voltage_to_resistance(voltage) 
        return (-self.A + np.sqrt(self.A**2 - 4*self.B*(1-r/self.R0 )))/(2*self.B)

""" Tboard returns a linear temp of 5mv/deg C"""
class Tboard (TemperatureSensor):

    def __init__(self, pin, sensorConfiguration, name):

        self.pin = pin
        self.name = name
        self.voltage_pr_degree = float(sensorConfiguration[1])
        logging.debug("Initialized temperature sensor at {0} with temp/deg = {1}".format(pin, sensorConfiguration[1]))


    def get_temperature(self, voltage):
        return voltage/self.voltage_pr_degree
