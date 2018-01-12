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
from PWM import PWM
from configobj import Section
import logging
from threading import Thread

from TemperatureControl import Unit, ConstantControl


class Fan(Unit):
    
    def __init__(self, name, options, printer):
        """
        channel : channel that this fan is on
        fan_id : number of the fan
        printer : description of this printer 
        """
        
        self.name = name
        self.options = options
        self.printer = printer
        
        self.input = self.options["input"]
        self.channel = int(self.options["channel"])
        self.force_disable = False
        
        self.printer.fans.append(self)
        
        self.counter += 1
            
        return
        
    def connect(self, units):
        self.input = self.get_unit(self.input, units)
        
        if self.options["add-to-M106"] == "True":
            self.force_disable = True
            if not isinstance(self.input, ConstantControl):
                msg = "{} has a non-constant controller attached. For control by M106/M107 set config 'input' as a constant".format(self.name)
                logging.error(msg)
                raise RuntimeError(msg)
            
            self.printer.controlled_fans.append(self)
            logging.info("Added {} to M106/M107".format(self.name))
        

    def set_PWM_frequency(self, value):
        """ Set the amount of on-time from 0..1 """
        self.pwm_frequency = int(value)
        PWM.set_frequency(value)

    def set_value(self, value):
        """ Set the amount of on-time from 0..1 """
        self.value = value
        PWM.set_value(value, self.channel)
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
            self.set_value(self.input.get_power())            		 
            time.sleep(1)
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
        if self.force_disable:
            self.disabled = True
            self.enabled = False
            return
        self.enabled = True
        self.disabled = False
        self.t = Thread(target=self.run_controller, name=self.name)
        self.t.daemon = True
        self.t.start()	
        return