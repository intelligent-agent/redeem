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

class Heater(object):
    """
    A heater element that must keep temperature,
    either an extruder, a HBP or could even be a heated chamber
    """
    def __init__(self, thermistor, mosfet, name, onoff_control):
        """ Init """
        self.thermistor = thermistor
        self.mosfet = mosfet
        self.name = name                   # Name, used for debugging
        self.current_temp = 0.0
        self.target_temp = 0.0             # Target temperature (Ts). Start off. 
        self.last_error = 0.0              # Previous error term, used in calculating the derivative
        self.error_integral = 0.0          # Accumulated integral since the temperature came within the boudry
        self.error_integral_limit = 100.0  # Integral temperature boundary
        self.P = 1.0                      # Proportional 
        self.I = 0.0                      # Integral 
        self.D = 0.0                      # Derivative
        self.onoff_control = onoff_control  # If we use PID or ON/OFF control
        self.ok_range = 4.0
        self.prefix = ""
        self.current_time = time.time()
        self.prev_time = time.time()
        self.temperatures = []
        self.errors = []
        self.sleep = 0.1
        self.avg = max(int(1.0/self.sleep), 3)
        self.A = np.vstack([range(self.avg), np.ones(self.avg)]).T 

    def set_target_temperature(self, temp):
        """ Set the desired temperature of the extruder """
        self.target_temp = float(temp)

    def get_temperature(self):
        """ get the temperature of the thermistor"""
        return np.average(self.temperatures[-self.avg:])

    def is_target_temperature_reached(self):
        """ Returns true if the target temperature is reached """
        if self.target_temp == 0:
            return True
        err = abs(self.current_temp - self.target_temp)
        return err < self.ok_range

    def is_temperature_stable(self, seconds=10):
        """ Returns true if the temperature has been stable for n seconds """
        if len(self.temperatures) < int(seconds/self.sleep):
            return False
        if max(self.temperatures[-int(seconds/self.sleep):]) > (self.target_temp + self.ok_range):
            return False
        if min(self.temperatures[-int(seconds/self.sleep):]) < (self.target_temp - self.ok_range):
            return False
        return True

    def disable(self):
        """ Stops the heater and the PID controller """
        self.enabled = False
        # Wait for PID to stop
        self.t.join()
        self.mosfet.set_power(0.0)

    def enable(self):
        """ Start the PID controller """
        self.enabled = True
        self.t = Thread(target=self.keep_temperature)
        self.t.start()

    def keep_temperature(self):
        """ PID Thread that keeps the temperature stable """
        while self.enabled:
            self.current_temp = self.thermistor.get_temperature()
            self.temperatures.append(self.current_temp)
            error = self.target_temp-self.current_temp
            self.errors.append(error)

            # Use linear regression to find the error and derivative 
            y = self.errors[-self.avg:]
            if len(self.errors) >= self.avg:
                derivative, avg_error = np.linalg.lstsq(self.A, y)[0]
            else:
                avg_error = error
                derivative = 0

            #if self.name =="E":
            #    logging.debug("Err: "+str(error)+" avg err: "+str(avg_error)+" der: "+str(derivative))
            if self.onoff_control:
                if error > 1.0:
                    power = 1.0
                else:
                    power = 0.0
            else:
                if abs(error) > 15:  # Avoid windup
                    if error > 0:
                        power = 1.0
                    else:
                        power = 0.0

                    self.error_integral = 0
                    self.last_error = error
                else:
                    #derivative = self._getErrorDerivative(error)
                    integral = self._getErrorIntegral(error)
                    power = self.P*(avg_error + self.D*derivative + self.I*integral)  # The standard formula for the PID				
                    power = max(min(power, 1.0), 0.0)                           # Normalize to 0,1

            # If the Thermistor is disconnected or running away or something
            if self.current_temp <= 5 or self.current_temp > 250:
                power = 0
            self.mosfet.set_power(power)
            time_diff = self.current_time-self.prev_time
            if time_diff > 2:
                logging.warning("Heater time update large: " +
                                self.name + " temp: " +
                                str(self.current_temp) + " time delta: " +
                                str(self.current_time-self.prev_time))
            self.prev_time = self.current_time
            self.current_time = time.time()
            time.sleep(self.sleep)

    def _getErrorDerivative(self, current_error):
        """ Get the derivative of the error term """
        derivative = (current_error-self.last_error)/self.sleep		# Calculate the diff
        self.last_error = current_error					      # Update the last error 
        return derivative

    def _getErrorIntegral(self, error):
        """ Calculate and return the error integral """
        self.error_integral += error*self.sleep
        return self.error_integral


class Extruder(Heater):
    """ Subclass for Heater, this is an extruder """
    def __init__(self, smd, thermistor, mosfet, name, onoff_control):
        Heater.__init__(self, thermistor, mosfet, name, onoff_control)
        self.smd = smd
        self.sleep = 0.1
        self.enable()


class HBP(Heater):
    """ Subclass for heater, this is a Heated build platform """
    def __init__(self, thermistor, mosfet, onoff_control):
        Heater.__init__(self, thermistor, mosfet, "HBP", onoff_control)
        self.sleep = 0.5 # Heaters have more thermal mass
        self.enable()
