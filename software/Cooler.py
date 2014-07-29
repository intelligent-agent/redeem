'''
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
'''

from threading import Thread
import time
import logging


class Cooler:
    ''' Init '''
    def __init__(self, cold_end, fan, name, onoff_control):
        self.cold_end = cold_end
        self.fan = fan             
        self.name = name                   # Name, used for debugging
        self.current_temp = 0.0
        self.target_temp = 0.0             # Target temperature (Ts). Start off. 
        self.last_error = 0.0              # Previous error term, used in calculating the derivative
        self.error_integral = 0.0          # Accumulated integral since the temperature came within the boudry
        self.error_integral_limit = 40.0  # Integral temperature boundry
        self.P = 1.0                      # Proportional 
        self.I = 0.0                      # Integral 
        self.D = 0.0                      # Derivative
        self.onoff_control = onoff_control #If we use PID or ON/OFF control
        self.ok_range = 4.0

    ''' Set the desired temperature of the extruder '''
    def set_target_temperature(self, temp):
        self.target_temp = float(temp)

    ''' get the temperature of the thermistor'''
    def get_temperature(self):
        return self.current_temp

    ''' Returns true if the target temperature is reached '''
    def is_target_temperature_reached(self):
        if self.target_temp  == 0:
          return True
        err = abs(self.current_temp - self.target_temp)
        return (err < self.ok_range)

    ''' Stops the heater and the PID controller '''
    def disable(self):
        self.enabled = False
        # Wait for PID to stop
        while self.disabled == False:
            time.sleep(0.2)
        # The PID loop has finished		
        self.fan.set_power(0.0)

    ''' Start the PID controller '''
    def enable(self):
        self.enabled = True
        self.disabled = False
        self.t = Thread(target=self.keep_temperature)
        self.t.daemon = True
        self.t.start()		

    ''' Set values for Proportional, Integral, Derivative'''
    def set_p_value(self, P):
        self.P = P # Proportional 

    def set_i_value(self, I):
        self.I = I # Integral

    def set_d_value(self, D):
        self.D = D # Derivative

    ''' PID Thread that keeps the temperature stable '''
    def keep_temperature(self):
        while self.enabled:            			
            self.current_temp = self.cold_end.get_temperature()    
            error = self.target_temp-self.current_temp    
            
            if self.onoff_control:
                if error>1.0:
                    power=1.0
                else:
                    power=0.0
            else:
                if abs(error)>10: #Avoid windup
                    if error>0:
                        power=1.0
                    else:
                        power=0.0

                    self.error_integral = 0
                    self.last_error = error
                else:
                    derivative = self._getErrorDerivative(error)            
                    integral = self._getErrorIntegral(error)     
                    power = self.P*(error + self.D*derivative + self.I*integral)  # The formula for the PID				
                    power = max(min(power, 1.0), 0.0)                             # Normalize to 0,1

            # If the Thermistor is disconnected or running away or something
            if self.current_temp <= 5 or self.current_temp > 250:
                power = 0.0
        
            power = 1.0-power
            #logging.debug("temp: "+str(self.current_temp)+" error: "+str(error)+" Cooler "+str(power))
            self.fan.set_value(power)            		 
            time.sleep(1)
        self.disabled = True


    ''' Get the derivative of the error term '''
    def _getErrorDerivative(self, current_error):       
        derivative = current_error-self.last_error		# Calculate the diff
        self.last_error = current_error					      # Update the last error 
        return derivative

    ''' Calculate and return the error integral '''
    def _getErrorIntegral(self, error):
        self.error_integral += error
        if self.current_temp < (self.target_temp-self.error_integral_limit):
            self.error_integral = 0.0
        if self.current_temp > (self.target_temp+self.error_integral_limit):
            self.error_integral = 0.0
        return self.error_integral

