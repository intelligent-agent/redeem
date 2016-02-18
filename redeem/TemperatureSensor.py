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
                self.sensor = Thermistor(pin, s)
                found = True
                break

        if found == False:
            for p in TemperatureSensorConfigs.pt100:
                if p[0] == self.sensorIdentifier:
                    logging.warning("PT100 temperature sensors are not supported yet.")
                    """ Not working yet. No known hardware solution """
                    #self.sensor = PT100((pin, heater_name, s
                    #found = True
                    break

        if found == False:
            Alarm(Alarm.THERMISTOR_ERROR, "The specified temperature sensor {0} is not implemented. You may add it's config in TemperatureSensorConfigs.".format(sensorIdentifier))

    """
    Returns the current temperature in degrees celsius for the given sensor.
    """
    def get_temperature(self):
        voltage = self.read_adc()
        return self.sensor.get_temperature(voltage)


    """
    Reads the adc pin and returns the actual voltage value
    Returns -1 if the reading is out of range.
    """
    def read_adc(self):
        mutex = Lock()
        voltage = -1.0

        mutex.acquire()
        try:
            with open(self.pin, "r") as file:
                signal = float(file.read().rstrip())
                if(signal >= self.maxAdc or signal <= 0.0):
                    voltage = -1.0
                else:
                    voltage = signal / 4094.0 * 1.8 #input range is 0 ... 1.8V
        except IOError as e:
             Alarm(Alarm.THERMISTOR_ERROR, "Unable to get ADC value ({0}): {1}".format(e.errno, e.strerror))
        finally:
            mutex.release()

        return voltage


""" This class represents standard thermistor sensors.
    It borrows heavily from Smoothieware's code (https://github.com/Smoothieware/Smoothieware).
    wolfmanjm, thanks!
"""
class Thermistor(TemperatureSensor):

    def __init__(self, pin, sensorConfiguration):
        """ Init """
        if len(sensorConfiguration) != 5:
            logging.error("Sensor configuration is missing parameters. Should have 5, has "+len(sensorConfiguration))
            sys.exit()
        else:
            self.pin = pin
            self.r1 = sensorConfiguration[1]    #pullup resistance
            self.c1 = sensorConfiguration[2]    #Steinhart-Hart coefficient
            self.c2 = sensorConfiguration[3]    #Steinhart-Hart coefficient
            self.c3 = sensorConfiguration[4]    #Steinhart-Hart coefficient



    def get_temperature(self, voltage):
        """ Return the temperature in degrees celsius. Uses Steinhart-Hart """
        r = self.voltage_to_resistance(voltage)
        l = math.log(r)
        t = (1.0 / (self.c1 + self.c2 * l + self.c3 * math.pow(l,3))) - 273.15
        return t

    def voltage_to_resistance(self,voltage):
        """ Convert the voltage to a resistance value """
        if voltage == 0 or (abs(voltage - 1.8) < 0.001):
            return 10000000.0
        return self.r1 / ((1.8 / voltage) - 1.0)


"""
This class represents PT100 temperature sensors
Caution: This code is not functional. It's merely a note of some ideas

"""
class PT100(TemperatureSensor):

    def __init__(self, pin, sensorConfiguration):

        if len(sensorConfiguration) != 4:
                logging.error("Sensor configuration is missing parameters. Should have 6, has "+len(sensorConfiguration))
                sys.exit()
        else:
            self.pin = pin
            self.name = name
            self.r0 = sensorConfiguration[1]
            self.a = sensorConfiguration[2]
            self.b = sensorConfiguration[3]


    def get_t(self, voltage):
        if voltage == 0 or (abs(voltage - 1.8) < 0.001):
            return 10000000.0

        #BIG questionmark: Is this right?
        r = float((self.r0 / (maxAdc / adc)) - 1.0)

        t = float(-self.r0*self.a
                    + math.sqrt(
                        math.pow(self.r0,2)*math.pow(self.a,2)
                        - 4*self.r0*self.b*(self.r0 - r))
                    / (2 * self.r0 * self.b))
        return t


#class ThermoCouple (TemperatureSensor):
