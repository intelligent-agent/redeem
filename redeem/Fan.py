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

from Adafruit_I2C import Adafruit_I2C 
import time
import subprocess
from PWM import PWM

class Fan(PWM):

    def __init__(self, channel):
        """ Channel is the channel that the fan is on (0-7) """
        self.channel = channel

    def set_value(self, value):
        """ Set the amount of on-time from 0..1 """
        PWM.set_value(value, self.channel)

if __name__ == '__main__':
    import os
    import logging

    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%m-%d %H:%M')

    PWM.set_frequency(100)   

    fan7 = Fan(7) 
    fan8 = Fan(8)
    fan9 = Fan(9)
    fan10 = Fan(10)


    while 1:    
        for i in xrange(1,100):
            fan7.set_value(i/100.0)
            fan8.set_value(i/100.0)
            fan9.set_value(i/100.0)
            fan10.set_value(i/100.0)
            time.sleep(0.01)	
        for i in xrange(100,1,-1):
            fan7.set_value(i/100.0)
            fan8.set_value(i/100.0)
            fan9.set_value(i/100.0)
            fan10.set_value(i/100.0)
            time.sleep(0.01)


