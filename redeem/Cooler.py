"""
A Cooler is a P controller 
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

class Cooler:

    def __init__(self, cold_end, fan, name, onoff_control):
        """ Init """
        self.cold_end = cold_end
        self.fan = fan
        self.name = name                   # Name, used for debugging
        self.current_temp = 0.0
        self.target_temp = 0.0             # Target temperature (Ts). Start off. 
        self.P = 1.0                      # Proportional 
        self.onoff_control = onoff_control # If we use PID or ON/OFF control
        self.ok_range = 4.0

    def set_target_temperature(self, temp):
        """ Set the desired temperature of the extruder """
        self.target_temp = float(temp)

    def get_temperature(self):
        """ get the temperature of the thermistor"""
        return self.current_temp

    def is_target_temperature_reached(self):
        """ Returns true if the target temperature is reached """
        if self.target_temp == 0:
            return True
        err = abs(self.current_temp - self.target_temp)
        return err < self.ok_range

    def disable(self):
        """ Stops the heater and the PID controller """
        self.enabled = False
        # Wait for PID to stop
        while self.disabled == False:
            time.sleep(0.2)
        # The PID loop has finished
        self.fan.set_power(0.0)

    def enable(self):
        """ Start the PID controller """
        self.enabled = True
        self.disabled = False
        self.t = Thread(target=self.keep_temperature)
        self.t.daemon = True
        self.t.start()		

    def set_p_value(self, P):
        """ Set values for Proportional, Integral, Derivative"""
        self.P = P # Proportional

    def keep_temperature(self):
        """ PID Thread that keeps the temperature stable """
        while self.enabled:
            self.current_temp = self.cold_end.get_temperature()    
            error = self.target_temp-self.current_temp    
            
            if self.onoff_control:
                power = 1.0 if (self.P*error > 1.0) else 0.0
            else:
                power = self.P*error  # The formula for the PID (only P)				
                power = max(min(power, 1.0), 0.0)                             # Normalize to 0,1

            # If the Thermistor is disconnected or running away or something
            if self.current_temp <= 5 or self.current_temp > 250:
                power = 0.0

            # Invert the control since it'a a cooler
            power = 1.0 - power
            #logging.info("Err: {}, Pwr: {}".format(error, power))
            self.fan.set_value(power)            		 
            time.sleep(1)
        self.disabled = True



