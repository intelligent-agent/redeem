#!/usr/bin/env python
"""
A fan is for blowing stuff away. This one is for Replicape.

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
import logging

#==============================================================================
# 
#==============================================================================

class Unit:
    printer = None
    def get_input(self, get):
        """
        get the correct input
        """
        # try to get it from the config
        if self.printer.config.has_section(get):
            input_type = self.printer.config.get(get, "type")
            return control_units[input_type](get, self.printer)
        
        # check thermistors and cold ends
        if "thermistor-" in get:
            g = get.replace("thermistor-","")
            if g in self.printer.thermistors:
                return self.printer.thermistors[g]
        elif "ds18b20" in get:
            for sensor in self.printer.cold_ends:
                if get == sensor.name:
                    return sensor
                    
        # can't find it, assume it is a number
        logging.info("Setting up fan controller. Cannot find {}. Assume it is a number".format(get))
        
        try:
            value = float(get)
        except:
            msg = "Setting up fan controller. Cannot convert '{}' to float".format(get)
            raise RuntimeError(msg)
            
        
        return value

class Alias(Unit):
    
    def __init__(self, name, printer):
        
        self.name = name
        self.printer = printer
        input_name = printer.config.get(name, "input")
        self.alias_input = self.get_input(input_name)
        
        return
        
    def get_temperature(self):
        return self.alias_input.get_temperature()
        
class Compare(Unit):
    def __init__(self, name, printer):
        self.printer = printer
        self.name = name
        self.inputs = []
        for i in range(2):
            input_name = printer.config.get(name, "input-{}".format(i))
            self.inputs.append(self.get_input(input_name))
        return
    
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
    
    def __init__(self, name, printer):
        self.name = name
        self.printer = printer
        input_name = printer.config.get(name, "input")
        self.control_input = self.get_input(input_name)
        
        self.get_options()
        
        return
        
class OnOffControl(Control):
        
    def get_options(self):
        
        # options
        self.on_temperature = self.printer.config.getfloat(self.name, 'on_temperature')
        self.off_temperature = self.printer.config.getfloat(self.name, 'off_temperature')
        self.on_power = self.printer.config.getint(self.name, 'on_power')/255.0
        self.off_power = self.printer.config.getint(self.name, 'off_power')/255.0
        
        self.power = self.off_power
        
        return
        
    def get_power(self):

        temp = self.control_input.get_temperature()
        
        if temp >= self.on_temperature:
            self.power = self.on_power
        elif temp <= self.off_temperature:
            self.power = self.off_power
        
        return self.power
        
class ProportionalControl(Control):

    def get_options(self):
        """ Init """
        self.current_temp = 0.0
        self.target_temp = self.printer.config.getfloat(self.name, 'target_temperature')             # Target temperature (Ts). Start off. 
        self.P = self.printer.config.getfloat(self.name, 'proportional')                     # Proportional 
        self.max_speed = self.printer.config.getfloat(self.name, 'max_speed')/255.0
        self.min_speed = self.printer.config.getfloat(self.name, 'min_speed')/255.0
        self.ok_range = self.printer.config.getfloat(self.name, 'ok_range')

    def get_power(self):
        """ PID Thread that keeps the temperature stable """
        self.current_temp = self.control_input.get_temperature()
        error = self.target_temp-self.current_temp
        
        print "error = ",error
        
        if error <= self.ok_range:
            return 0.0
        
        power = self.P*error  # The formula for the PID (only P)		
        power = max(min(power, 1.0), 0.0)                             # Normalize to 0,1
        
        # Invert the control since it'a a cooler
        power = 1.0 - power
        
        # Clamp the max speed
        power = min(power, self.max_speed)
        # Clamp min speed
        power = max(power, self.min_speed)
        
        return power

###        
        
class Fan(Unit): #class Fan(PWM):
    
    def __init__(self, channel, fan_id, printer):
        """
        channel : channel that this fan is on
        fan_id : number of the fan
        printer : description of this printer 
        """
        
        self.channel = channel
        self.printer = printer
        
        config = printer.config
        
        self.name = "Fan-{}".format(fan_id)
        input_name = config.get(self.name, "value")
        
        self.fan_input = self.get_input(input_name)
        
        if isinstance(self.fan_input, float):
            value = min(abs(float(self.fan_input))/255.0, 1.0)
            self.set_value(value)
        elif isinstance(self.fan_input, Control):
            self.enable() # start the fan controller
        else:
            msg = "Fan input {} is not a number [0..255] or a control unit".format(self.fan_input)
            logging.error(msg)
            raise RuntimeError(msg)
            
        return

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
            self.set_value(self.fan_input.get_power())            		 
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
        self.enabled = True
        self.disabled = False
        self.t = Thread(target=self.run_controller, name=self.name)
        self.t.daemon = True
        self.t.start()	
        return
        
###
        
control_units = {"alias":Alias, "difference":Difference, 
                      "maximum":Maximum, "minimum":Minimum, 
                      "on-off-control":OnOffControl,
                      "proportional-control":ProportionalControl}

###
        
#==============================================================================
# EXAMPLE
#==============================================================================

#[AmbientTemperature]
#type = alias
#input = ds18b20-1
#
#[CoolantTemperature]
#type = alias
#input = ds18b20-0
#
#[CoolantWarmup]
#type = difference
#input-0 = AmbientTemperature
#input-1 = CoolantTemperature
#
#[CoolantFan]
#type = proportional-control
#input = CoolantWarmup
#target_temperature = 0
#proportional = 0.1
#max_speed = 255
#min_speed = 50
#ok_range = 2
#
#[EitherHotend]
#type = maximum
#input-0 = thermistor-A
#input-1 = thermistor-B
#
#[CoolantPump]
#type = on-off-control
#input = EitherHotend
#on_temperature = 80
#off_temperature = 60
#on_power = 100
#off_power = 0
#					  
#[Fan-0]
#value = CoolantPump
#
#[Fan-1]
#value = CoolantFan
#
#[Fan-2]
#value = 127
#
#[Fan-3]
#value = 255
