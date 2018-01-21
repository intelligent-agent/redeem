#!/usr/bin/env python
"""
A single PWM channel or timer on the AM335x. 

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

""" 
"""
class PWM_pin(object):
    def __init__(self, pin, frequency, duty_cycle): 
        if pin == "P9_14":
            self.chip = 0
            self.channel = 0
        elif pin == "P9_16":
            self.chip = 0
            self.channel = 1
        elif pin == "0:0":
            self.chip = 0
            self.channel = 0
        elif pin == "0:1":
            self.chip = 0
            self.channel = 1
        elif pin == "2:0":
            self.chip = 2
            self.channel = 0
        elif pin == "2:1":
            self.chip = 2
            self.channel = 1
        elif pin == "4:0":
            self.chip = 4
            self.channel = 0
        elif pin == "5:0":
            self.chip = 5
            self.channel = 0
        elif pin == "6:0":
            self.chip = 6
            self.channel = 0
        elif pin == "7:0":
            self.chip = 7
            self.channel = 0
        else:
            logging.warning("Unrcognized pin '{}'. You may have to implement it...".format(pin))


        self.enabled = False
        self.export_chip(self.chip, self.channel)
        self.set_frequency(frequency)
        self.set_value(duty_cycle)
        
    def export_chip(self, chip, channel):
        self.base = "/sys/class/pwm/pwmchip{}/pwm-{}:{}".format(chip, chip, channel)
        if not os.path.exists(self.base):
            with open("/sys/class/pwm/pwmchip{}/export".format(chip), "w") as f:
                f.write(str(channel))
            if not os.path.exists(self.base):
                logging.warning("Unable to export PWM pin")
        

    def set_enabled(self, is_enabled = True):
        if self.enabled == is_enabled:
            return
        path = self.base+"/enable"
        with open(path, "w") as f:           
            f.write("1" if is_enabled else "0")
        self.enabled = is_enabled


    def set_frequency(self, freq):
        """ Set the PWM frequency for all fans connected on this PWM-chip """
        # period is specified in picoseconds
        period = int( (1.0/float(freq))*(10**9) )
        self.period = period
        path = self.base+"/period"
        logging.debug("Setting period to "+str(period))
        with open(path, "w") as f:
            f.write(str(period))

    def set_value(self, value):
        """ Set the amount of on-time from 0..1 """
        duty_cycle = int(self.period*float(value))
        path = self.base+"/duty_cycle"
        #logging.debug("Setting duty_cycle to "+str(duty_cycle))
        with open(path, "w") as f:
            f.write(str(duty_cycle))
        # Call enable/disable here since the timer pins 
        self.set_enabled( (value > 0) )


    def ramp_to(self, value, delay=0.01):
        ''' Set the fan/light value to the given value, in degree, with the given speed in deg / sec '''
        for w in xrange(int(self.value*255.0), int(value*255.0), (1 if value>=self.value else -1)):
            self.set_value(w/255.0)
            time.sleep(delay)
        self.set_value(value)


if __name__ == '__main__':
   
    p1 = PWM_pin("P9_14", 50, 0.1)
    p2 = PWM_pin("P9_16", 50, 0.1)
    
    while 1:
        for i in range(100):
            p1.set_value(0.1+(i*0.001))
            p2.set_value(0.1+(i*0.001))
            time.sleep(0.03)
        for i in range(100):
            p1.set_value(0.2-(i*0.001))
            p2.set_value(0.2-(i*0.001))
            time.sleep(0.03)


