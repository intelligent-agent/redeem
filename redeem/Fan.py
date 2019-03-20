#!/usr/bin/env python
"""
A fan is for blowing stuff away. This one is for Replicape.

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
import time
from six import PY2

if PY2:
  range = xrange


class Fan(object):
  def __init__(self, pwm_output):
    self.pwm = pwm_output

  def set_PWM_frequency(self, value):
    """ Set the amount of on-time from 0..1 """
    self.pwm_frequency = int(value)
    self.pwm.set_frequency(value)

  def set_value(self, value):
    """ Set the amount of on-time from 0..1 """
    self.value = value
    self.pwm.set_value(value)

  def ramp_to(self, value, delay=0.01):
    ''' Set the fan/light value to the given value, in degree, with the given speed in deg / sec '''
    for w in range(int(self.value * 255.0), int(value * 255.0), (1 if value >= self.value else -1)):
      logging.debug("Fan value: " + str(w))
      self.set_value(w / 255.0)
      time.sleep(delay)
    self.set_value(value)
