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
    """
    A list of specified size that overwrites the oldest data when space 
    runs out. 

    https://stackoverflow.com/a/40784706
    """
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
        """ Get the current length of the list"""
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
    """
    Base component of all temperature control units
    """
    
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
            unit = ConstantControl(c_name, {"value":int(name)}, self.printer)
            units[c_name] = unit
            return unit

        
        return
        
    def initialise(self):
        """ perform post connection initialization"""
        return
        
    def check(self):
        """ run any checks that need to be performed after full initialisation"""
        return
        
    def __str__(self):
        return self.name
                        
        
class Alias(Unit):
    """
    Used as an alias for another unit
    """
    
    def __init__(self, name, options, printer):
        """ initialize the unit """
        
        self.name = name
        self.options = options
        self.printer = printer
        
        self.input = self.options["input"]
            
        self.counter += 1
        
        return
        
    def connect(self, units):
        """ connect to other units """
        self.input = self.get_unit(self.input, units)
        
    def get_value(self):
        """ return the current value """
        return self.input.get_value()
        
    def check(self):
        """ perform any checks or logging after full connection """
        logging.info("{} --> {} ".format(self.input, self.name))
        
        
class Compare(Unit):
    """
    Perform an operation on two inputs
    """
    
    def __init__(self, name, options, printer):
        """ initialize the unit """
        self.name = name
        self.options = options
        self.printer = printer
        
        self.input = []
        for i in range(2):
            self.input.append(options["input-{}".format(i)])
            
        self.counter += 1
            
        return
    
    def connect(self, units):
        """ connect to other units """
        for i in range(2):
            self.input[i] = self.get_unit(self.input[i], units)
            
    def check(self):
        """ perform any checks or logging after full connection """
        logging.info("({} and {}) --> {}".format(self.input[0].name, self.input[1].name, self.name))
    
    
class Difference(Compare):
    """ Calculate the difference between inputs""" 
    def get_value(self):
        """ return the current value """
        return self.input[0].get_value() - self.input[1].get_value()
        
        
class Maximum(Compare):
    """ Calculate the maximum of two inputs"""
    def get_value(self):
        """ return the current value """
        return max(self.input[0].get_value(), self.input[1].get_value())
        
        
class Minimum(Compare):
    """ Calculate the minimum of two inputs"""
    def get_value(self):
        """ return the current value """
        return min(self.input[0].get_value(), self.input[1].get_value())

class Safety(Unit):
    """
    Perform safety related checks based on the temperature of the attached
    sensor and raise appropriate alarms
    """
    
    def __init__(self, name, options, printer):
        """ initialize the unit """
        self.name = name
        self.options = options
        self.printer = printer
        
        self.input = options["input"]
        self.heater = options["heater"]
        
        self.min_temp           = float(self.options["min_temp"])         # If temperature falls below this point from the target, disable. 
        self.max_temp           = float(self.options["max_temp"])         # Max temp that can be reached before disabling printer. 
        self.max_rise_rate      = float(self.options["max_rise_rate"])    # Fastest temp can rise pr measrement
        self.max_fall_rate      = float(self.options["max_fall_rate"])    # Fastest temp can fall pr measurement
        self.min_rise_rate      = float(self.options["min_rise_rate"])    # Slowest temp can rise pr measurement, to catch incorrect attachment of thermistor
        self.min_rise_offset    = float(self.options["min_rise_offset"])  # Allow checking for slow temp rise when temp is below this offset from target temp 
        self.min_rise_delay     = float(self.options["min_rise_delay"])   # Allow checking for slow temp rise after this delay time to allow for heat soak
        
        self.min_temp_enabled = False
        
        return
        
    def connect(self, units):
        """ connect to other units """
        self.input = self.get_unit(self.input, units)
        self.heater = self.get_unit(self.heater, units)
        return
        
    def initialise(self):
        """ perform post connection initialization"""
        # insert into the attached heater, if it isn't already there
        if not self.heater.safety:
            self.heater.safety = [self]
        elif self not in self.heater.safety:
            self.heater.safety.append(self)
            
        input_sensor = self.input
        if isinstance(self.input, Alias):
            input_sensor = self.input.input
    
        disconnect = False
        if (not isinstance(input_sensor, TemperatureSensor)) and (not isinstance(input_sensor, ColdEnd)):
            msg = "{} disabled. {} is not a temperature sensor".format(self.name, self.input.name)
            logging.warning(msg)
            disconnect = True
            
        # disconnect from the heater
        if disconnect:
            for i, s in enumerate(self.heater.safety):
                if self == s:
                    self.heater.safety.pop(i)
                    break
                
            return
                
                
        self.avg = max(int(1.0/self.heater.input.sleep), 5)
        self.temp = CircularBuffer(self.avg)
        self.time = CircularBuffer(self.avg)
                        
        return
        
    def check(self):
        """ perform any checks or logging after full connection """
        logging.info("{} --> {} --> {}".format(self.input.name, self.name, self.heater.name))
        
    def set_min_temp_enabled(self, flag):
        """ enable the min_temp flag """
        self.min_temp_enabled = flag
        
    def run_safety_checks(self):
        """ Check the temperatures, make sure they are sane. 
        Sound the alarm if something is wrong """
        
        # add to ring buffers
        self.time.append(time.time())
        self.temp.append(self.input.get_value())
        
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
        target_temp = self.heater.input.target_value
        power_on = self.heater.mosfet.get_power() > 0
        
        # track when the heater was first turned on
        if target_temp == 0.0:
            self. start_heating_time = time.time()
        heating_time = current_time - self.start_heating_time
        
        # Check that temperature is not rising too quickly
        if temp_rate > self.max_rise_rate:
            a = Alarm(Alarm.HEATER_RISING_FAST, 
                "Temperature rising too quickly ({:.2f} degrees/sec) for {} ({} = {:.2f})".format(temp_rate, self.name, self.input.name, current_temp))
        
        
        # Check that temperature is not rising quickly enough when power is applied
        check = [temp_rate < self.min_rise_rate, 
                 power_on, 
                 current_temp < (target_temp - self.min_rise_offset), 
                 heating_time > self.min_rise_delay]
        if np.all(check):
            a = Alarm(Alarm.HEATER_RISING_SLOW, 
                "Temperature rising too slowly ({:.2f} degrees/sec) for {} ({} = {:.2f})".format(temp_rate, self.name, self.input.name, current_temp))
        # Check that temperature is not falling too quickly
        if temp_rate < -self.max_fall_rate:
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
    """
    Control schemes base class
    """
    
    def __init__(self, name, options, printer):
        """ initialize the unit """
        self.name = name
        self.options = options
        self.printer = printer
        
        self.input = None
        self.output = None
        
        self.value = 0.0
        self.sleep = 0.25
        
        self.get_options()
        
        self.counter += 1
        
        return
        
    def get_options(self):
        """ retrieve options from config"""
            
        return
        
    def connect(self, units):
        """ connect to other units """
        self.input = self.get_unit(self.input, units)
        if self.output:
            self.output = self.get_unit(self.output, units)
            self.output.input = self
        
        return
        
    def reset(self):
        """ reset any historical data """
        return
        
    def check(self):  
        """ perform any checks or logging after full connection """
        logging.info("{} --> {} --> {}".format(self.input, self.name, self.output))
            
        
class ConstantControl(Control):
    """
    Return a constant value for control applications
    """
    
    feedback_control = False
    
    def get_options(self):
        """ retrieve options from config"""
        
        self.output = None
        if "output" in self.options:
            self.output = self.options["output"]
            
        self.value = int(self.options['value'])/255.0
        return
        
    def connect(self, units):
        """ connect to other units """
        if self.output:
            self.output = self.get_unit(self.output, units)
            self.output.input = self
        
        
    def get_value(self):
        """ return the current value """
        return self.value
        
    def set_target_value(self, value):
        """ set the desired value """
        self.value = float(value)
        
    def ramp_to(self, value, delay):
        """ ramp the control output up to 'value' by 1/255 every 'delay' seconds"""
        save_sleep = self.sleep
        self.sleep = delay/2.0
        for w in range(int(self.value*255.0), int(value*255.0), (1 if value >= self.value else -1)):
            self.value = w/255.0
            time.sleep(delay)
        self.value = value
        self.sleep = save_sleep
        
    
    def check(self):
        """ perform any checks or logging after full connection """
        logging.info("{} --> {} --> {}".format(self.value, self.name, self.output))
        
        

class CommandCode(ConstantControl):
    """ 
    For connecting G and M codes
    """
        
    def get_options(self):
        """ retrieve options from config"""
        self.command = [c.strip() for c in self.options["command"].split(",")]
        for command in self.command:
            if command in self.printer.command_connect:
                logging.warning("multiple instances of {} used in [Temperature Control]".format(self.command))
            self.printer.command_connect[command] = self
        
        self.output = []
        if "output" in self.options:
            self.output = [o.strip() for o in self.options["output"].split(",")]
            
        self.input = self.command
        
        
    def connect(self, units):
        """ connect to other units """
        for i, output in enumerate(self.output):
            self.output[i] = self.get_unit(output, units)
            self.output[i].input = self
            
    def check(self):
        """ perform any checks or logging after full connection """
        outputs = "["
        for output in self.output:
            outputs += "{}, ".format(output)
        outputs = outputs[0:-2] + "]"
        logging.info("{} --> {} --> {}".format(self.input, self.name, outputs))
            
    def __str__(self):
        return str(self.name)
        
        
class OnOffControl(Control):
    """
    Control by switching between two defined states
    """
    
    feedback_control = True
        
    def get_options(self):
        """ retrieve options from config"""
        self.input = self.options["input"]
        self.output = None
        if "output" in self.options:
            self.output = self.options["output"]
        self.target_value = float(self.options['target_value'])
        self.on_offset = float(self.options['on_offset'])
        self.off_offset = float(self.options['off_offset'])
        self.max_value = float(self.options['on_value'])/255.0
        self.off_value = float(self.options['off_value'])/255.0
        self.sleep = float(self.options['sleep'])
        
        self.ok_range = abs(self.on_offset)
        
        self.value = self.off_value
        
        return
        
    def set_target_value(self, value):
        """ set the target value """
        self.target_value = float(value)
        return
        
    def get_target_value(self):
        """ get the target value """
        return self.target_value
        
    def get_value(self):
        """ return the current value """
        value = self.input.get_value()
        
        if value <= (self.target_value + self.on_offset):
            self.value = self.max_value
        elif value >= (self.target_value + self.off_offset):
            self.value = self.off_value
        
        return self.value
        
        
class ProportionalControl(Control):
    """
    Control output in proportion to the instantaneous error between current 
    and target value
    """
    
    feedback_control = True

    def get_options(self):
        """ retrieve options from config"""
        self.input = self.options["input"]
        self.output = None
        if "output" in self.options:
            self.output = self.options["output"]
        self.current_value = 0.0
        self.target_value = float(self.options['target_value'])             # Target value (Ts). Start off. 
        self.P = float(self.options['proportional'])                     # Proportional 
        self.max_value = min(1.0, float(self.options['max_value'])/255.0)
        self.min_value = max(0, float(self.options['min_value'])/255.0)
        self.ok_range = float(self.options['ok_range'])
        self.sleep = float(self.options['sleep'])
        
    def set_target_value(self, value):
        """ set the target value """
        self.target_value = float(value)
        return
        
    def get_target_value(self):
        """ get the target value """
        return self.target_value

    def get_value(self):
        """ return the current value based on proportional (P) control"""
        self.current_value = self.input.get_value()
        error = self.target_value-self.current_value
        
        if error <= self.ok_range:
            return 0.0
        
        value = self.P*error  # The formula for the PID (only P)		
        value = max(min(value, 1.0), 0.0)                             # Normalize to 0,1
        
        # Clamp the max value
        value = min(value, self.max_value)
        # Clamp min value
        value = max(value, self.min_value)
        
        return value
        
class PIDControl(Control):
    """
    Control output according to proportional (P), integral (I) and 
    derivative (D) terms.
    """
    
    feedback_control = True
    
    def get_options(self):
        """ retrieve options from config"""
        self.input = self.options["input"]
        self.output = None
        if "output" in self.options:
            self.output = self.options["output"]
        self.target_value = float(self.options['target_value'])
        self.Kp = float(self.options['pid_Kp'])
        self.Ti = float(self.options['pid_Ti'])
        self.Td = float(self.options['pid_Td'])
        self.ok_range = float(self.options['ok_range'])
        self.max_value = min(1.0, float(self.options['max_value'])/255.0)
        self.sleep = float(self.options['sleep'])
        
        self.on_off_range = np.inf
        if "on_off_range" in self.options:
            self.on_off_range = float(self.options['on_off_range'])
        
        return
        
    def initialise(self):
        """ perform post connection initialization"""
        self.avg = max(int(1.0/self.sleep), 3)
        self.error = 0
        self.errors = [0]*self.avg
        self.averages = [0]*self.avg
        
        current_value = self.input.get_value()
        self.values = [current_value]
        
        self.error_integral = 0.0           # Accumulated integral since the value came within the boudry
        self.error_integral_limit = 100.0   # Integral value boundary
        
    
    def set_target_value(self, value):
        """ set the target value """
        self.target_value = float(value)
        return
        
    def get_target_value(self):
        """ get the target value """
        return self.target_value
        
        
    def get_value(self):
        """ return the current value based on PID control"""
        current_value = self.input.get_value()
        self.values.append(current_value)
        self.values[:-max(int(60/self.sleep), self.avg)] = [] # Keep only this much history

        self.error = self.target_value-current_value
        self.errors.append(self.error)
        self.errors.pop(0)
        
        if self.error > self.on_off_range:
            # on off control
            self.reset()
            value = self.max_value
        else:
            # pid control
            derivative = self.get_error_derivative()
            integral = self.get_error_integral()
            # The standard formula for the PID
            value = self.Kp*(self.error + (1.0/self.Ti)*integral + self.Td*derivative)  
            value = max(min(value, self.max_value, 1.0), 0.0)                         # Normalize to 0, max

        return value
        
    def get_error_derivative(self):
        """ Get the derivative of the value"""
        # Using value and not error for calculating derivative 
        # gets rid of the derivative kick. dT/dt
        der = (self.values[-2]-self.values[-1])/self.sleep
        self.averages.append(der)
        if len(self.averages) > 11:
            self.averages.pop(0)
        return np.average(self.averages)

    def get_error_integral(self):
        """ Calculate and return the error integral """
        self.error_integral += self.error*self.sleep
        # Avoid windup by clippping the integral part 
        # to the reciprocal of the integral term
        self.error_integral = np.clip(self.error_integral, 0, self.max_value*self.Ti/self.Kp)
        return self.error_integral
        
    def reset(self):
        """ reset any historical values """
        
        self.error_integral = 0.0
        
        return
        
    def set_Kp(self, kp):
        """ redefine the Kp value """
        self.Kp = kp
        self.options["pid_Kp"] = kp
        
    def set_Ti(self, ti):
        """ redefine the Ti value """
        self.Ti = ti
        self.options["pid_Ti"] = ti
        
    def set_Td(self, td):
        """ redefine the Td value """
        self.Td = td
        self.options["pid_Td"] = td
        
    
