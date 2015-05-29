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

from PWM import PWM

class DAC(PWM):

    def __init__(self, channel):
        """ Channel is the pwm output is on (0..15) """
        self.channel = channel
        self.offset = 0.0

    def set_voltage(self, voltage):
        """ Set the amount of on-time from 0..1 """
        # The VCC on the PWM chip is 5.0V on Replicape Rev B1
        PWM.set_value((voltage/5.0)+self.offset, self.channel)


if __name__ == '__main__':
    PWM.set_frequency(100)

    dacs = [0]*5
    for i in range(5):
        dacs[i] = DAC(11+i)
        dacs[i].set_voltage(1.5)

