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
        """ retrieve a thermistor, cold_end, mosfet, or unit"""
        
        # check if we already have what we are looking for
        if isinstance(name, Unit):
            return name
        
        # check units, thermistors, and cold ends
        if name in units:
            return units[name]
        elif "Thermistor" in name:
            if name in self.printer.thermistors:
                return self.printer.thermistors[name]
        elif "MOSFET" in name:
            if name in self.printer.mosfets:
                return self.printer.mosfets[name]
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
        
    def initialise(self):
        """ stuff to do after connecting"""
        
        #        
        
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
        
        self.power = 0.0
        
        self.get_options()
        
        self.counter += 1
        
        return
        
    def connect(self, units):
        self.input = self.get_unit(self.input, units)
        if self.output:
            self.output = self.get_unit(self.output, units)
            self.output.input = self
        
        return
            
        
class ConstantControl(Control):
    
    feedback_control = False
    
    def get_options(self):
        self.power = int(self.options['input'])/255.0
        return
        
    def get_power(self):
        return self.power
        
        
class OnOffControl(Control):
    
    feedback_control = True
        
    def get_options(self):
        self.on_temperature = float(self.options['on_temperature'])
        self.off_temperature = float(self.options['off_temperature'])
        self.on_power = float(self.options['on_power'])/255.0
        self.off_power = float(self.options['off_power'])/255.0
        
        self.power = self.off_power
        
        return
        
    def get_power(self):

        temp = self.input.get_temperature()
        
        if temp <= self.on_temperature:
            self.power = self.on_power
        elif temp >= self.off_temperature:
            self.power = self.off_power
        
        return self.power
        
        
class ProportionalControl(Control):
    
    feedback_control = True

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
        
class PIDControl(Control):
    
    feedback_control = True
    
    def get_options(self):
        
        self.Kp = float(self.options['pid_Kp'])
        self.Ti = float(self.options['pid_Ti'])
        self.Td = float(self.options['pid_Td'])
        self.ok_range = float(self.options['ok_range'])
        self.sleep = float(self.options['sleep'])
        
        return
        
    def initialise(self):
        
        self.avg = max(int(1.0/self.sleep), 3)
        self.error = 0
        self.errors = [0]*self.avg
        self.averages = [0]*self.avg
        
        current_temp = self.input.get_temperature()
        self.temperatures = [current_temp]
        
        self.error_integral = 0.0           # Accumulated integral since the temperature came within the boudry
        self.error_integral_limit = 100.0   # Integral temperature boundary
        
        
    def get_power(self):
        
        current_temp = self.input.get_temperature()
        self.temperatures.append(current_temp)
        self.temperatures[:-max(int(60/self.sleep), self.avg)] = [] # Keep only this much history

        self.error = self.target_temp-current_temp
        self.errors.append(self.error)
        self.errors.pop(0)

        derivative = self.get_error_derivative()
        integral = self.get_error_integral()
        # The standard formula for the PID
        power = self.Kp*(self.error + (1.0/self.Ti)*integral + self.Td*derivative)  
        power = max(min(power, self.max_power, 1.0), 0.0)                         # Normalize to 0, max

        return power
        
    def get_error_derivative(self):
        """ Get the derivative of the temperature"""
        # Using temperature and not error for calculating derivative 
        # gets rid of the derivative kick. dT/dt
        der = (self.temperatures[-2]-self.temperatures[-1])/self.sleep
        self.averages.append(der)
        if len(self.averages) > 11:
            self.averages.pop(0)
        return np.average(self.averages)

    def get_error_integral(self):
        """ Calculate and return the error integral """
        self.error_integral += self.error*self.sleep
        # Avoid windup by clippping the integral part 
        # to the reciprocal of the integral term
        self.error_integral = np.clip(self.error_integral, 0, self.max_power*self.Ti/self.Kp)
        return self.error_integral
        
    def reset(self):
        
        self.error_integral = 0.0
        
        return
        
