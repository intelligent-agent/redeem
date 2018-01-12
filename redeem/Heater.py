"""
Extruder file for Replicape.

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

from threading import Thread
import time
import logging
import numpy as np
from Alarm import Alarm

from TemperatureControl import Unit, Control, PIDControl

class Heater(Unit):
    """
    A heater element that must keep temperature,
    either an extruder, a HBP or could even be a heated chamber
    """
    def __init__(self, name, options, printer):
        """ Init """

        self.name = name
        self.options = options
        self.printer = printer        
        
        self.thermistor = self.options["temperature"]
        self.mosfet = self.options["mosfet"]
        self.prefix = self.options["prefix"]
        self.sleep = float(self.options["sleep"])                    # Time to sleep between measurements
        
        
        self.max_power          = float(self.options["max_power"])                # Maximum power
        self.min_temp_enabled   = False  # Temperature error limit 
        self.min_temp           = float(self.options["min_temp"])      # If temperature falls below this point from the target, disable. 
        self.max_temp           = float(self.options["max_temp"])  # Max temp that can be reached before disabling printer. 
        self.max_temp_rise      = float(self.options["max_rise_temp"])    # Fastest temp can rise pr measrement
        self.min_temp_rise      = float(self.options["min_rise_temp"])    # Slowest temp can rise pr measurement, to catch incorrect attachment of thermistor
        self.max_temp_fall      = float(self.options["max_fall_temp"])    # Fastest temp can fall pr measurement
        
        
        self.input = self.options["input"]

        self.heater_error = False
        
        self.thermistor_temperatures = []
        self.control_temperatures = []
        
        return

    def connect(self, units):
        """ connect to sensors and control units"""

        # connect the thermistor
        self.thermistor = self.get_unit(self.thermistor, units)
        
        # connect a MOSFET
        self.mosfet = self.printer.mosfets[self.name.replace("Heater", "MOSFET")]
        
        # connect the controller
        self.input = self.get_unit(self.input, units)

        return
        
    def initialise(self):
        """ stuff to do after connecting"""
        
        if not self.thermistor.sensor:
            logging.warning("{} temperature sensor is not set, heater disabled".format(self.name))
            self.heater_error = True
        
        # ensure the controller is one that allows feedback, i.e. not open loop        
        allow = False
        if isinstance(self.input, Control):
            if self.input.feedback_control:
                allow = True
        if not allow:
            self.mosfet.set_power(0.0)
            logging.error("{} has non-feedback control assigned, heater disabled".format(self.name))
            self.heater_error = True
        
        # if the thermistor is not the input to the controller driving this heater generate a warning
        if self.thermistor != self.input.input:
            logging.warning("{} control driven by {}".format(self.name, self.input.input.name))
        
        # inherit the sleep timer from PID controller if that is what we are using
        if isinstance(self.input, PIDControl):
            self.sleep = self.input.sleep
        
        return

    def set_target_temperature(self, temp):
        """ Set the target temperature of the controller """
        self.min_temp_enabled = False
        self.input.target_temperature = float(temp)

    def get_temperature(self):
        """ get the temperature of the thermistor and the control input"""
        therm = np.average(self.thermistor_temperatures[-self.avg:])
        control = np.average(self.control_temperatures[-self.avg:])
        return therm, control

    def get_temperature_raw(self):
        """ Get unaveraged temp measurement """
        return self.thermistor_temperatures[-1], self.control_temperatures[-1]

    def get_target_temperature(self):
        """ get the target temperature"""
        return self.input.target_temperature

    def is_target_temperature_reached(self):
        """ Returns true if the target temperature is reached """
        
        current_temp = self.control_temperatures[-1]
        target_temp = self.input.target_temperature
        
        if target_temp == 0:
            return True
        if current_temp == 0:
            self.input.target_temperature = 0
            target_temp = 0
        err = abs(current_temp - target_temp)
        reached = err < self.input.ok_range
        return reached

    def is_temperature_stable(self, seconds=10):
        """ Returns true if the temperature has been stable for n seconds """
        target_temp = self.input.target_temperature
        ok_range = self.input.ok_range
        if len(self.control_temperatures) < int(seconds/self.sleep):
            return False
        if max(self.control_temperatures[-int(seconds/self.sleep):]) > (target_temp + ok_range):
            return False
        if min(self.control_temperatures[-int(seconds/self.sleep):]) < (target_temp - ok_range):
            return False
        return True

    def get_noise_magnitude(self, measurements=10):
        """ Calculate and return the magnitude in the noise """
        measurements = min(measurements, len(self.temperatures))
        #logging.debug("Measurements: "+str(self.temperatures))
        avg = np.average(self.control_temperatures[-measurements:])
        mag = np.max(self.control_temperatures[-measurements:])
        #logging.debug("Avg: "+str(avg))
        #logging.debug("Mag: "+str(mag))
        return abs(mag-avg)

    def set_min_temp(self, min_temp):
        """ Set the minimum temperature. If current temp goes below this, 
        sound the alarm """
        self.current_min_temp = min_temp
    
    def enable_min_temp(self):
        """ Enable minimum temperature alarm """
        self.min_temp_enabled = True
        logging.info("Min temp alarm enabled at {} for {}".format(self.min_temp, self.name))
    
    def disable(self):
        """ Stops the heater and the PID controller """
        self.input.target_temperature = 0
        self.enabled = False
        self.mosfet.set_power(0.0)
        # Wait for PID to stop
        self.t.join()
        logging.debug("{} disabled".format(self.name))
        self.mosfet.set_power(0.0)
        self.input.reset()


    def enable(self):
        """ Start the PID controller """
        if self.heater_error:
            self.enabled = False
            return
        self.avg = max(int(1.0/self.sleep), 3)
        self.prev_time = self.current_time = time.time()
        self.thermistor_temperatures = [self.thermistor.get_temperature()]  
        self.control_temperatures = [self.input.input.get_temperature()]
        self.enabled = True
        self.t = Thread(target=self.run_controller, name=self.name)
        self.t.start()

    def run_controller(self):
        """ thread to run the controller in """
        try:
            while self.enabled:
                
                # get the controllers recommendation
                power = self.input.get_power()
                power = max(min(power, self.max_power, 1.0), 0.0)
                
                # get the attached thermistor temperature
                therm_temp = self.thermistor.get_temperature()
                self.thermistor_temperatures.append(therm_temp)
                self.thermistor_temperatures[:-max(int(60/self.sleep), self.avg)] = [] # Keep only this much history
                
                # get the controlling temperature
                cntrl_temp = self.input.input.get_temperature()
                self.control_temperatures.append(cntrl_temp)
                self.control_temperatures[:-max(int(60/self.sleep), self.avg)] = [] # Keep only this much history

                # Run safety checks
                self.time_diff = self.current_time-self.prev_time
                self.prev_time = self.current_time
                self.current_time = time.time()

                if not self.heater_error:
                    self.check_temperature_error()

                # Set temp if temperature is OK
                if not self.heater_error and therm_temp > 0:
                    self.mosfet.set_power(power)
                else:
                    self.mosfet.set_power(0)        
                time.sleep(self.sleep)
        finally:
            # Disable this mosfet if anything goes wrong
            self.mosfet.set_power(0)

    def check_temperature_error(self):
        """ Check the temperatures, make sure they are sane. 
        Sound the alarm if something is wrong """
        temps = self.thermistor_temperatures
        current_temp = temps[-1]
        if len(temps) < 2:
            return
        temp_delta = temps[-1]-temps[-2]
        # Check that temperature is not rising too quickly
        if temp_delta > self.max_temp_rise:
            a = Alarm(Alarm.HEATER_RISING_FAST, 
                "Temperature rising too quickly ({} degrees) for {}".format(temp_delta, self.name))
        # Check that temperature is not rising quickly enough when power is applied
        if (temp_delta < self.min_temp_rise) and (self.mosfet.get_power() > 0):
            a = Alarm(Alarm.HEATER_RISING_SLOW, 
                "Temperature rising too slowly ({} degrees) for {}".format(temp_delta, self.name))
        # Check that temperature is not falling too quickly
        if temp_delta < -self.max_temp_fall:
            a = Alarm(Alarm.HEATER_FALLING_FAST, 
                "Temperature falling too quickly ({} degrees) for {}".format(temp_delta, self.name))
        # Check that temperature has not fallen below a certain setpoint from target
        if self.min_temp_enabled and self.current_temp < (self.target_temp - self.min_temp):
            a = Alarm(Alarm.HEATER_TOO_COLD, 
                "Temperature below min set point ({} degrees) for {}".format(self.min_temp, self.name), 
                "Alarm: Heater {}".format(self.name))
        # Check if the temperature has gone beyond the max value
        if self.current_temp > self.max_temp:
            a = Alarm(Alarm.HEATER_TOO_HOT, 
                "Temperature beyond max ({} degrees) for {}".format(self.max_temp, self.name))                
        # Check the time diff, only warn if something is off.     
        if self.time_diff > 4:
            logging.warning("Heater time update large: " +
                            self.name + " temp: " +
                            str(current_temp) + " time delta: " +
                            str(self.current_time-self.prev_time))
