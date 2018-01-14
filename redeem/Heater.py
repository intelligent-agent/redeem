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
        
        self.mosfet = self.options["mosfet"]
        self.prefix = self.options["prefix"]
        
        self.safety = [s.strip() for s in options["safety"].split(",")]
        self.min_temp_enabled   = False  # Temperature error limit 
        
        self.input = self.options["input"]

        self.heater_error = False
        
        self.temperatures = []
        
        # add to printer
        self.short_name = self.name.split("-")[-1]
        self.printer.heaters[self.short_name] = self
        
        return

    def connect(self, units):
        """ connect to sensors and control units"""
        
        # connect a MOSFET
        self.mosfet = self.printer.mosfets[self.short_name]
        
        # connect the controller
        self.input = self.get_unit(self.input, units)
        
        #connect the safety
        for i, s in enumerate(self.safety):
            self.safety[i] = self.get_unit(s, units)

        return
        
    def initialise(self):
        """ stuff to do after connecting"""
        
        # inherit the sleep timer from controller
        self.sleep = self.input.sleep
        self.max_power = self.input.max_power
            
        return
        
    def check(self):
        """ run checks"""

        if not self.safety:
            self.mosfet.set_power(0.0)
            logging.warning("{} has no safety connected, heater disabled".format(self.name))
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
        
        return

    def set_target_temperature(self, temp):
        """ Set the target temperature of the controller """
        self.min_temp_enabled = False
        self.input.set_target_temperature(temp)

    def get_temperature(self):
        """ get the temperature of the thermistor and the control input"""
        return np.average(self.temperatures[-self.avg:])

    def get_temperature_raw(self):
        """ Get unaveraged temp measurement """
        return self.temperatures[-1]

    def get_target_temperature(self):
        """ get the target temperature"""
        return self.input.get_target_temperature()

    def is_target_temperature_reached(self):
        """ Returns true if the target temperature is reached """
        
        current_temp = self.temperatures[-1]
        target_temp = self.get_target_temperature()
        
        if target_temp == 0:
            return True
        if current_temp == 0:
            self.set_target_temperature(0)
            target_temp = 0
        err = abs(current_temp - target_temp)
        reached = err < self.input.ok_range
        return reached

    def is_temperature_stable(self, seconds=10):
        """ Returns true if the temperature has been stable for n seconds """
        target_temp = self.get_target_temperature()
        ok_range = self.input.ok_range
        if len(self.temperatures) < int(seconds/self.sleep):
            return False
        if max(self.temperatures[-int(seconds/self.sleep):]) > (target_temp + ok_range):
            return False
        if min(self.temperatures[-int(seconds/self.sleep):]) < (target_temp - ok_range):
            return False
        return True

    def get_noise_magnitude(self, measurements=10):
        """ Calculate and return the magnitude in the noise """
        measurements = min(measurements, len(self.temperatures))
        #logging.debug("Measurements: "+str(self.temperatures))
        avg = np.average(self.temperatures[-measurements:])
        mag = np.max(self.temperatures[-measurements:])
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
        self.set_target_temperature(0)
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
        self.temperatures = [self.input.input.get_temperature()]
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
                
                # get the controlling temperature
                temp = self.input.input.get_temperature()
                self.temperatures.append(temp)
                self.temperatures[:-max(int(60/self.sleep), self.avg)] = [] # Keep only this much history

                # Run safety checks

                if not self.heater_error:
                    self.check_temperature_error()

                # Set temp if temperature is OK
                if not self.heater_error:
                    self.mosfet.set_power(power)
                else:
                    self.mosfet.set_power(0)        
                time.sleep(self.sleep)
        finally:
            # Disable this mosfet if anything goes wrong
            self.mosfet.set_power(0)
            self.set_target_temperature(0.0)

    def check_temperature_error(self):
        """ for errors according to the attached safety units """
        
        for s in self.safety:
            s.set_min_temp_enabled(self.min_temp_enabled)
            s.run_safety_checks()
