#!/usr/bin/env python
"""
This is an implementation of the PWM DAC
It has a second order low pass filter 
giving a ripple voltage of less than 1 mV

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

import time
import logging


class PWM_DAC(object):
  """ This class implements a DAC using a PWM and a second order low pass filter """

  def __init__(self, pwm_output):
    """ Channel is the pwm output is on (0..15) """
    self.pwm = pwm_output
    self.offset = 0.0

  def set_voltage(self, voltage):
    """ Set the amount of on-time from 0..1 """
    # The VCC on the PWM chip is 5.0V on Replicape Rev B1
    self.pwm.set_value((voltage / 5.0) + self.offset)


class DAC(object):
  """ This class uses an actual DAC """

  def __init__(self, spi, channel):
    """ Channel is the pwm output is on (0..15) """
    self.spi = spi
    self.channel = channel
    self.offset = 0.0

  def set_voltage(self, voltage):
    logging.debug("Setting voltage to " + str(voltage))

    v_ref = 3.3    # Voltage reference on the DAC
    dacval = int((voltage * 256.0) / v_ref)
    byte1 = int(((dacval & 0xF0) >> 4) | (self.channel << 4))
    byte2 = int((dacval & 0x0F) << 4)
    self.spi.writebytes([byte1, byte2])    # Update all channels
    self.spi.writebytes([0xA0, 0xFF])
