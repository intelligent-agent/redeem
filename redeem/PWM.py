#!/usr/bin/env python
"""
This is an implementation of the PWM DAC

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

from Adafruit_GPIO.I2C import Device as I2C

import time
import subprocess
import logging
import os
import glob


class PWM_Output(object):
  def set_value(self, value):
    raise NotImplementedError()


class PWM_PCA9685_Output(PWM_Output):
  def __init__(self, controller, channel):
    self.controller = controller
    self.channel = channel

  def set_value(self, value):
    self.controller.set_value(self.channel, value)


class PWM_PCA9685(object):

  frequency = 0
  i2c = None

  PCA9685_MODE1 = 0x0
  PCA9685_PRESCALE = 0xFE

  def __init__(self, i2c_address, i2c_bus):
    self.i2c = I2C(i2c_address, i2c_bus)
    self.i2c.write8(self.PCA9685_MODE1, 0x01)    # Reset
    self.i2c._logger.setLevel(logging.WARNING)

  def set_frequency(self, freq):
    """ Set the PWM frequency for all fans connected on this PWM-chip """
    prescaleval = 25000000
    prescaleval /= 4096
    prescaleval /= float(freq)
    prescaleval = int(prescaleval + 0.5)
    prescaleval -= 1

    oldmode = self.i2c.readU8(self.PCA9685_MODE1)
    newmode = (oldmode & 0x7F) | 0x10
    self.i2c.write8(self.PCA9685_MODE1, newmode)
    self.i2c.write8(self.PCA9685_PRESCALE, prescaleval)
    self.i2c.write8(self.PCA9685_MODE1, oldmode)
    time.sleep(0.05)
    self.i2c.write8(self.PCA9685_MODE1, oldmode | 0xA1)

    self.frequency = freq

  def set_value(self, channel, value):
    """ Set the amount of on-time from 0..1 """
    off = int(value * 4095)
    byte_list = [0x00, 0x00, off & 0xFF, off >> 8]
    self.i2c.writeList(0x06 + (4 * channel), byte_list)

  def get_output(self, channel):
    return PWM_PCA9685_Output(self, channel)
