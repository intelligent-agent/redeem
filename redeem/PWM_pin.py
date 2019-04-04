#!/usr/bin/env python
"""
This is an implementation of the PWM pin for servos

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
import subprocess
import os
import logging
import Adafruit_BBIO.PWM as PWM
""" 
"""


class PWM_pin:
  def __init__(self, pin, frequency, duty_cycle):
    self.pin = pin

    # Adafruit takes duty cycles as percentages
    PWM.start(pin, duty_cycle * 100, frequency)

  def set_frequency(self, freq):
    """ Set the PWM frequency for all fans connected on this PWM-chip """
    PWM.set_frequency(self.pin, freq)

  def set_value(self, value):
    """ Set the amount of on-time from 0..1 """
    PWM.set_duty_cycle(self.pin, value * 100)


if __name__ == '__main__':

  p1 = PWM_pin("P9_14", 50, 0.1)
  p2 = PWM_pin("P9_16", 50, 0.1)

  while 1:
    for i in range(100):
      p1.set_value(0.1 + (i * 0.001))
      p2.set_value(0.1 + (i * 0.001))
      time.sleep(0.03)
    for i in range(100):
      p1.set_value(0.2 - (i * 0.001))
      p2.set_value(0.2 - (i * 0.001))
      time.sleep(0.03)
