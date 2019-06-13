#!/usr/bin/env python
"""
A board current measurment sensor class for Reevolve boards.

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
from Alarm import Alarm
from TemperatureSensor import TemperatureSensor

class ADCSensor:
  def __init__(self, pin):
    self.pin = pin
    self.max_adc = 4095.0

  def get_voltage(self):
    voltage = 0

    TemperatureSensor.mutex.acquire()
    try:
     with open(self.pin, "r") as file:
       signal = float(file.read().rstrip())
       if (signal > self.max_adc or signal <= 0.0):
         voltage = -1.0
       else:
         voltage = signal / self.max_adc * 1.8    #input range is 0 ... 1.8V
    except IOError as e:
     Alarm(Alarm.SENSOR_ERROR, "Unable to get ADC value ({0}): {1}".format(
         e.errno, e.strerror))
    TemperatureSensor.mutex.release()
    return voltage

class VoltageSensor(ADCSensor):
  def __init__(self, pin):
      ADCSensor.__init__(self, pin)

  def get_value(self):
      R1 = 100000.0
      R2 = 4700.0
      v_out = self.get_voltage()
      return ((R1+R2)*v_out)/R2

class CurrentSensor(ADCSensor):
  def __init__(self, pin):
    ADCSensor.__init__(self, pin)

  def get_value(self):
    v_out = self.get_voltage()
    return v_out * 1000.0 / 50.0
