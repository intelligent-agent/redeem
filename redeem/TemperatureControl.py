#!/usr/bin/env python
"""
Implementation of a system for controlling heating and cooling on the 
replicape. Essentially consists of building blocks for creating a network of 
functional units that connects temperature sensors to heating/cooling units.

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

#==============================================================================
# CLASSES
#==============================================================================

class Unit:
    
    printer = None
    counter = 0
    
    def get_unit(self, name, units):
        """ retrieve a thermistor, cold_end, or unit"""
        
        # check units, thermistors, and cold ends
        if name in units:
            return units[name]
        elif "thermistor-" in name:
            g = name.replace("thermistor-","")
            if g in self.printer.thermistors:
                return self.printer.thermistors[g]
        elif "ds18b20" in name:
            for sensor in self.printer.cold_ends:
                if name == sensor.name:
                    return sensor
        else: #assume it is a constant
            c_name = "Constant-{}".format(self.counter)
            unit = ConstantControl(c_name, {"input":int(name)}, self.printer)
            units[c_name] = unit
            return unit

        
        return
                        
        
class Alias(Unit):
    
    def __init__(self, name, options, printer):
        
        self.name = name
        self.options = options
        self.printer = printer
        self.input = options["input"]
        
        self.output = None
        if "output" in options:
            self.output = options["output"]
            
        self.counter += 1
        
        return
        
    def connect(self, units):
        self.input = self.get_unit(self.input, units)
        if self.output:
            self.output = self.get_unit(self.output, units)
            self.output.input = self
        
    def get_temperature(self):
        return self.input.get_temperature()
        
        
class Compare(Unit):
    def __init__(self, name, options, printer):
        self.name = name
        self.options = options
        self.printer = printer
        self.inputs = []
        for i in range(2):
            self.inputs.append(options["input-{}".format(i)])
            
        self.output = None
        if "output" in options:
            self.output = options["output"]
            
        self.counter += 1
            
        return
    
    def connect(self, units):
        for i in range(2):
            self.inputs[i] = self.get_unit(self.inputs[i], units)
        if self.output:
            self.output = self.get_unit(self.output, units)
            self.output.input = self
    
    
class Difference(Compare):
    def get_temperature(self):
        return self.inputs[0].get_temperature() - self.inputs[1].get_temperature()
        
        
class Maximum(Compare):
    def get_temperature(self):
        return max(self.inputs[0].get_temperature(), self.inputs[1].get_temperature())
        
        
class Minimum(Compare):
    def get_temperature(self):
        return min(self.inputs[0].get_temperature(), self.inputs[1].get_temperature())
        
        
class Control(Unit):
    
    def __init__(self, name, options, printer):
        self.name = name
        self.options = options
        self.printer = printer
        self.input = options["input"]
        
        self.output = None
        if "output" in options:
            self.output = options["output"]
        
        self.get_options()
        
        self.counter += 1
        
        return
        
    def connect(self, units):
        self.input = self.get_unit(self.input, units)
        if self.output:
            self.output = self.get_unit(self.output, units)
            self.output.input = self
            
        
class ConstantControl(Control):
    
    def get_options(self):
        self.power = int(self.options['input'])/255.0
        return
        
    def get_power(self):
        return self.power
        
        
class OnOffControl(Control):
        
    def get_options(self):
        self.on_temperature = float(self.options['on_temperature'])
        self.off_temperature = float(self.options['off_temperature'])
        self.on_power = float(self.options['on_power'])/255.0
        self.off_power = float(self.options['off_power'])/255.0
        
        self.power = self.off_power
        
        return
        
    def get_power(self):

        temp = self.input.get_temperature()
        
        if temp >= self.on_temperature:
            self.power = self.on_power
        elif temp <= self.off_temperature:
            self.power = self.off_power
        
        return self.power
        
        
class ProportionalControl(Control):

    def get_options(self):
        """ Init """
        self.current_temp = 0.0
        self.target_temp = float(self.options['target_temperature'])             # Target temperature (Ts). Start off. 
        self.P = float(self.options['proportional'])                     # Proportional 
        self.max_speed = float(self.options['max_speed'])/255.0
        self.min_speed = float(self.options['min_speed'])/255.0
        self.ok_range = float(self.options['ok_range'])

    def get_power(self):
        """ PID Thread that keeps the temperature stable """
        self.current_temp = self.input.get_temperature()
        error = self.target_temp-self.current_temp
        
        if error <= self.ok_range:
            return 0.0
        
        power = self.P*error  # The formula for the PID (only P)		
        power = max(min(power, 1.0), 0.0)                             # Normalize to 0,1
        
        # Clamp the max speed
        power = min(power, self.max_speed)
        # Clamp min speed
        power = max(power, self.min_speed)
        
        return power

###        
        
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

#==============================================================================
# FUNCTIONS
#==============================================================================

def build_temperature_control(printer):
    """ build the network linking sensors to controllers """
    
    control_units = {"alias":Alias, "difference":Difference, 
                      "maximum":Maximum, "minimum":Minimum,
                      "constant-control":ConstantControl,
                      "on-off-control":OnOffControl,
                      "proportional-control":ProportionalControl,
                      "fan":Fan}
    
    units = {}
    for section in ["Temperature Control", "Fans"]: #, Heaters]: TODO
        cfg = printer.config[section]
    
        # generate units
        for name, options in cfg.items():
            if not isinstance(options, Section):
                continue
            input_type = options["type"]
            unit = control_units[input_type](name, options, printer)
            units[name] = unit
        
    # connect units
    for name, unit in units.items():
        unit.connect(units)
    
    return
