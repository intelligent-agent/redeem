#!/usr/bin/env python
"""
For running a fan.

Author: Daryl Bond
email: daryl(dot)bond(at)hotmail(dot)com
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
from builtins import range
from PWM import PWM_PCA9685, PWM_AM335
from configobj import Section
import logging
from threading import Thread

from TemperatureControl import Unit, ConstantControl

#class Fan(PWM):

class Fan(Unit):
    """
    Used to move air
    """
    AM335 = 0
    PCA9685 = 1

    def __init__(self, name, options, printer):
        """
        Fan initialization.
        """
        
        self.name = name
        self.options = options
        self.printer = printer

        self.input = None
        if "input" in self.options:
            self.input = self.options["input"]
            
        self.channel = int(self.options["channel"])
        logging.debug(options)
        # get fan index
        i = int(name[-1])
        
        self.printer.fans[i] = self
        self.max_value = 1.0
        
        self.counter += 1
            
        return
        
    def connect(self, units):
        """ Connect this unit to other units"""
        if self.input:
            self.input = self.get_unit(self.input, units)
            if not self.input.output:        
                self.input.output = self
            
    def check(self):
        """ Perform any checks or logging after all connections are made"""
        logging.info("{} --> {}".format(self.input, self.name))
            
        

    def set_PWM_frequency(self, value):
        """ Set the amount of on-time from 0..1 """
        self.pwm_frequency = int(value)
        PWM.set_frequency(value)

    def set_value(self, value):
        """ Set the amount of on-time from 0..1 """
        self.value = value
        if self.options["chip"] == Fan.PCA9685:
            PWM_PCA9685.set_value(value, self.channel)
        elif self.options["chip"] == Fan.AM335:
            PWM_PCA9685.set_value(value, self.channel)
        return


    def ramp_to(self, value, delay=0.01):
        ''' Set the fan/light value to the given value, in degree, with the given speed in deg / sec '''
        for w in range(int(self.value*255.0), int(value*255.0), (1 if value >= self.value else -1)):
            logging.debug("Fan value: "+str(w))
            self.set_value(w/255.0)
            time.sleep(delay)
        self.set_value(value)

    def run_controller(self):
        """ follow a target PWM value 0..1"""
        
        while self.enabled:
            self.set_value(self.input.get_value())            		 
            time.sleep(self.input.sleep)
        self.disabled = True

    def disable(self):
        """ stops the controller """
        self.enabled = False
        # Wait for controller to stop
        while self.disabled == False:
            time.sleep(0.2)
        # The controller loop has finished
        self.set_value(0.0)

    def enable(self):
        """ starts the controller """
        
        if not self.input:
            self.enabled = False
            self.disabled = True
            self.set_value(0.0)
            return
            
        self.enabled = True
        self.disabled = False
        self.t = Thread(target=self.run_controller, name=self.name)
        self.t.daemon = True
        self.t.start()	
        return
        
    def __str__(self):
        return self.name
