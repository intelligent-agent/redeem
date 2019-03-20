#!/usr/bin/env python
"""
A Mosfet class for setting the PWM of a power mosfet for Replicape.

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


class Mosfet(object):
  def __init__(self, pwm_output):
    self.pwm = pwm_output
    self.power = 0.0

  def set_power(self, value):
    self.power = value
    """Set duty cycle between 0 and 1"""
    self.pwm.set_value(value)

  def get_power(self):
    return self.power
