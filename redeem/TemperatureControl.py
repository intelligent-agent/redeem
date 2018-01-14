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
from configobj import Section
import logging
from threading import Thread
import numpy as np

from PWM import PWM
from Alarm import Alarm
from TemperatureSensor import TemperatureSensor
from ColdEnd import ColdEnd

#==============================================================================
# CLASSES
#==============================================================================

class CircularBuffer(object):
    #https://stackoverflow.com/a/40784706
    def __init__(self, size):
        """Initialization"""
        self.index = 0
        self.size = size
        self._data = []

    def append(self, value):
        """Append an element"""
        if len(self._data) == self.size:
            self._data[self.index] = value
        else:
            self._data.append(value)
        self.index = (self.index + 1) % self.size
        
    def get_length(self):
        return len(self._data)

    def __getitem__(self, key):
        """Get element by index, relative to the current index"""
        if len(self._data) == self.size:
            return(self._data[(key + self.index) % self.size])
        else:
            return(self._data[key])

    def __repr__(self):
        """Return string representation"""
        return self._data.__repr__() + ' (' + str(len(self._data))+' items)'

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
            e = name.split("-")[-1]
            return self.printer.thermistors[e]
        elif "MOSFET" in name:
            e = name.split("-")[-1]
            return self.printer.mosfets[name]
        elif "ds18b20" in name:
            for sensor in self.printer.cold_ends:
                if name == sensor.name:
                    return sensor
        else: #assume it is a constant
            c_name = "Constant-{}".format(self.counter)
            unit = ConstantControl(c_name, {"input":int(name), "sleep":1.0}, self.printer)
            units[c_name] = unit
            return unit

        
        return
        
    def initialise(self):
        """ stuff to do after connecting"""
        return
        
    def check(self):
        """ run any checks that need to be performed after full initialisation"""
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
        
        
class Safety(Unit):
    
    def __init__(self, name, options, printer):
        self.name = name
        self.options = options
        self.printer = printer
        
        self.input = options["input"]
        self.heater = options["heater"]
        
        self.min_temp           = float(self.options["min_temp"])         # If temperature falls below this point from the target, disable. 
        self.max_temp           = float(self.options["max_temp"])         # Max temp that can be reached before disabling printer. 
        self.max_temp_rise      = float(self.options["max_rise_temp"])    # Fastest temp can rise pr measrement
        self.max_temp_fall      = float(self.options["max_fall_temp"])    # Fastest temp can fall pr measurement
        self.min_temp_rise      = float(self.options["min_rise_temp"])    # Slowest temp can rise pr measurement, to catch incorrect attachment of thermistor
        self.min_rise_offset    = float(self.options["min_rise_offset"])  # Allow checking for slow temp rise when temp is below this offset from target temp 
        self.min_rise_delay     = float(self.options["min_rise_delay"])   # Allow checking for slow temp rise after this delay time to allow for heat soak
        
        self.min_temp_enabled = False
        
        return
        
    def connect(self, units):
        
        self.input = self.get_unit(self.input, units)
        self.heater = self.get_unit(self.heater, units)
        
        return
        
    def initialise(self):
        
        # insert into the attached heater, if it isn't already there
        if self not in self.heater.safety:
            self.heater.safety.append(self)
    
        if (not isinstance(self.input, TemperatureSensor)) and (not isinstance(self.input, ColdEnd)):
            msg = "{} will not work, input = {} is not a temperature sensor".format(self.name, self.input.name)
            logging.error(msg)
            
            # disconnect from the heater
            for i, s in enumerate(self.heater.safety):
                if self == s:
                    self.heater.safety.pop(i)
                    break
                
        self.avg = max(int(1.0/self.heater.input.sleep), 5)
        self.temp = CircularBuffer(self.avg)
        self.time = CircularBuffer(self.avg)
                        
        return
        
    def set_min_temp_enabled(self, flag):
        """ enable the min_temp flag """
        self.min_temp_enabled = flag
        
    def run_safety_checks(self):
        """ Check the temperatures, make sure they are sane. 
        Sound the alarm if something is wrong """
        
        # add to ring buffers
        self.time.append(time.time())
        self.temp.append(self.input.get_temperature())
        
        # get ordered lists
        times = [self.time[i] for i in range(self.time.get_length())]
        temps = [self.temp[i] for i in range(self.temp.get_length())]
        n = len(times)
        
        if not n == self.time.size:
            return
        
        # last recorded temperature
        current_time = times[-1]
        current_temp = sum(temps)/float(n) #average
        
        # rate of change of temperature wrt time
        temp_rate = np.polyfit(times, temps, 1)[0]
        time_delta = times[-1] - times[0]
        
        # heater info
        target_temp = self.heater.input.target_temperature
        power_on = self.heater.mosfet.get_power() > 0
        
        # track when the heater was first turned on
        if target_temp == 0.0:
            self. start_heating_time = time.time()
        heating_time = current_time - self.start_heating_time
        
        # Check that temperature is not rising too quickly
        if temp_rate > self.max_temp_rise:
            a = Alarm(Alarm.HEATER_RISING_FAST, 
                "Temperature rising too quickly ({:.2f} degrees/sec) for {} ({} = {:.2f})".format(temp_rate, self.name, self.input.name, current_temp))
        
        
        # Check that temperature is not rising quickly enough when power is applied
        check = [temp_rate < self.min_temp_rise, 
                 power_on, 
                 current_temp < (target_temp - self.min_rise_offset), 
                 heating_time > self.min_rise_delay]
        if np.all(check):
            a = Alarm(Alarm.HEATER_RISING_SLOW, 
                "Temperature rising too slowly ({:.2f} degrees/sec) for {} ({} = {:.2f})".format(temp_rate, self.name, self.input.name, current_temp))
        # Check that temperature is not falling too quickly
        if temp_rate < -self.max_temp_fall:
            a = Alarm(Alarm.HEATER_FALLING_FAST, 
                "Temperature falling too quickly ({:.2f} degrees/sec) for {} ({} = {:.2f})".format(temp_rate, self.name, self.input.name, current_temp))
        # Check that temperature has not fallen below a certain setpoint from target
        if self.min_temp_enabled and (current_temp < (target_temp - self.min_temp)):
            a = Alarm(Alarm.HEATER_TOO_COLD, 
                "Temperature of {:.2f} below min set point ({:.2f} degrees) for {}".format(current_temp, self.min_temp, self.name))
        # Check if the temperature has gone beyond the max value
        if current_temp > self.max_temp:
            a = Alarm(Alarm.HEATER_TOO_HOT, 
                "Temperature of {:.2f} beyond max ({:.2f} degrees) for {}".format(current_temp, self.max_temp, self.name))                
        # Check the time diff, only warn if something is off.     
        if time_delta > 4:
            logging.warning("Time between updates too large: " +
                            self.name + " temp: " +
                            str(current_temp) + " time delta: " +
                            str(time_delta))
        
        return
        
        
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
        
    def get_options(self):
        return
        
    def connect(self, units):
        self.input = self.get_unit(self.input, units)
        if self.output:
            self.output = self.get_unit(self.output, units)
            self.output.input = self
        
        return
        
    def reset(self):
        return
            
        
class ConstantControl(Control):
    
    feedback_control = False
    
    def get_options(self):
        self.power = int(self.options['input'])/255.0
        self.sleep = 1.0 # use a default
        return
        
    def get_power(self):
        return self.power
        
        
class OnOffControl(Control):
    
    feedback_control = True
        
    def get_options(self):
        self.target_temperature = float(self.options['target_temperature'])
        self.on_offset = float(self.options['on_offset'])
        self.off_offset = float(self.options['off_offset'])
        self.max_power = float(self.options['on_power'])/255.0
        self.off_power = float(self.options['off_power'])/255.0
        self.sleep = float(self.options['sleep'])
        
        self.on_temperature = self.target_temperature + self.on_offset
        self.off_temperature = self.target_temperature + self.off_offset
        
        self.power = self.off_power
        
        return
        
    def set_target_temperature(self, temp):
        """ set the target temperature """

        self.target_temperature = float(temp)
        self.on_temperature = self.target_temperature + self.on_offset
        self.off_temperature = self.target_temperature + self.off_offset
        
        return
        
    def get_target_temperature(self):
        """ get the target temperature """
        return self.target_temperature
        
    def get_power(self):

        temp = self.input.get_temperature()
        
        if temp <= self.on_temperature:
            self.power = self.max_power
        elif temp >= self.off_temperature:
            self.power = self.off_power
        
        return self.power
        
        
class ProportionalControl(Control):
    
    feedback_control = True

    def get_options(self):
        """ Init """
        self.current_temp = 0.0
        self.target_temperature = float(self.options['target_temperature'])             # Target temperature (Ts). Start off. 
        self.P = float(self.options['proportional'])                     # Proportional 
        self.max_power = min(1.0, float(self.options['max_power'])/255.0)
        self.min_power = max(0, float(self.options['min_power'])/255.0)
        self.ok_range = float(self.options['ok_range'])
        self.sleep = float(self.options['sleep'])
        
    def set_target_temperature(self, temp):
        """ set the target temperature """
        self.target_temperature = float(temp)
        return
        
    def get_target_temperature(self):
        """ get the target temperature """
        return self.target_temperature

    def get_power(self):
        """ PID Thread that keeps the temperature stable """
        self.current_temp = self.input.get_temperature()
        error = self.target_temperature-self.current_temp
        
        if error <= self.ok_range:
            return 0.0
        
        power = self.P*error  # The formula for the PID (only P)		
        power = max(min(power, 1.0), 0.0)                             # Normalize to 0,1
        
        # Clamp the max power
        power = min(power, self.max_power)
        # Clamp min power
        power = max(power, self.min_power)
        
        return power
        
class PIDControl(Control):
    
    feedback_control = True
    
    def get_options(self):
        
        self.target_temperature = float(self.options['target_temperature'])
        self.Kp = float(self.options['pid_Kp'])
        self.Ti = float(self.options['pid_Ti'])
        self.Td = float(self.options['pid_Td'])
        self.ok_range = float(self.options['ok_range'])
        self.max_power = min(1.0, float(self.options['max_power'])/255.0)
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
        
    
    def set_target_temperature(self, temp):
        """ set the target temperature """
        self.target_temperature = float(temp)
        return
        
    def get_target_temperature(self):
        """ get the target temperature """
        return self.target_temperature
        
        
    def get_power(self):
        
        current_temp = self.input.get_temperature()
        self.temperatures.append(current_temp)
        self.temperatures[:-max(int(60/self.sleep), self.avg)] = [] # Keep only this much history

        self.error = self.target_temperature-current_temp
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
        
