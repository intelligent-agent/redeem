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

from PWM import PWM_PCA9685,PWM_AM335
import logging

class Mosfet:
    def __init__(self, channel, chip_type):
        """ Channel is the channel that the thing is on (0-15) """
        self.channel = channel
        self.power = 0.0
        if chip_type == "AM335":
            self.chip = PWM_AM335(channel, 100, 0.0)
            self.chip_type = 0
        elif chip_type == "PCA9685":
            self.chip = PWM_PCA9685
            self.chip_type = 1

    def set_power(self, value):
        self.power = value
        """Set duty cycle between 0 and 1"""
        if self.chip_type == 0:
            self.chip.set_value(value)
        elif self.chip_type == 1:
            self.chip.set_value(value, self.channel)
        else:
            logging.error("Mosfet: Unknown PWM chip: {}".format(self.chip))    


    def get_power(self):
        return self.power

if __name__ == '__main__':

    PWM.set_frequency(1000)   

    mosfets = [0]*3
    for i in range(3):
        mosfets[i] = Mosfet(3+i)
        mosfets[i].set_power(0.25)

