'''
Extruder file for Replicape. 

Author: Elias Bakken
email: elias.bakken@gmail.com
Website: http://www.hipstercircuits.com
License: BSD

You can use and change this, but keep this heading :)
'''


import bbio as io
from threading import Thread

''' 
A heater element that must keep temperature, 
either an extruder, a HBP or could even be a heated chamer
'''
class Heater(object):
    ''' Init '''
    def __init__(self, thermistor, mosfet, name):
        self.thermistor = thermistor     # A handle to the thermistor instance used. 
        self.mosfet = mosfet             # A handle to the mosfet instance used. 
        self.name = name                 # Name, used for debugging
        self.current_temp = 0.0
        self.target_temp = 0.0             # Target temperature (Ts). Start off. 
        self.last_error = 0.0              # Previous error term, used in calculating the derivative
        self.error_integral = 0.0          # Accumulated integral since the temperature came within the boudry
        self.error_integral_limit = 10.0 # Integral temperature boundry
        self.debug = 0                   # Debug level
        self.P = 1.0                     # Proportional 
        self.I = 0.0                     # Integral 
        self.D = 0.0                     # Derivative

    ''' Set the desired temperature of the extruder '''
    def setTargetTemperature(self, temp):
        self.target_temp = float(temp)

    ''' get the temperature of the thermistor'''
    def getTemperature(self):
        return self.current_temp

    ''' Stops the heater and the PID controller '''
    def disable(self):
        self.enabled = False
        # Wait for PID to stop
        while self.disabled == False:
            io.delay(200)
        # The PID loop has finished		
        self.mosfet.setPower(0.0)
        self.mosfet.close()

    ''' Start the PID controller '''
    def enable(self):
        self.enabled = True
        self.disabled = False
        self.t = Thread(target=self.keep_temperature)
        self.t.start()		

    ''' Set values for Proportional, Integral, Derivative'''
    def setPvalue(self, P):
           self.P = P # Proportional 

    def setIvalue(self, I):
           self.I = I # Integral

    def setDvalue(self, D):
           self.D = D # Derivative

    ''' PID Thread that keeps the temperature stable '''
    def keep_temperature(self):
        while self.enabled:            			
            self.current_temp = self.thermistor.getTemperature()    # Read the current temperature		
            error = self.target_temp-self.current_temp   # Calculate the error 
            derivative = self._getErrorDerivative(error) # Calculate the error derivative 
            integral = self._getErrorIntegral(error)     # Calculate the error integral        
            power = self.P*(error + self.D*derivative + self.I*integral) # The formula for the PID				
            power = max(min(power, 1.0), 0.0)            # Normalize to 0,1
            self.mosfet.setPower(power)            		 # Update the mosfet
            if self.debug > 0:            				 # Debug if necessary 
                print self.name+": Target: %f, Current: %f"%(self.target_temp, self.current_temp),
                print ", error: %f, power: %f"%(error, power),
                print ", derivative: %f, integral: %f"%(self.D*derivative, self.I*integral)
            io.delay(1000)            					 # Wait one second        
        self.disabled = True							 # Signal the disable that we are done


    ''' Get the derivative of the error term '''
    def _getErrorDerivative(self, current_error):       
        derivative = current_error-self.last_error		# Calculate the diff
        self.last_error = current_error					# Update the last error 
        return derivative

    ''' Calculate and return the error integral '''
    def _getErrorIntegral(self, error):
        self.error_integral += error
        if self.current_temp < (self.target_temp-self.error_integral_limit):
            self.error_integral = 0.0
        if self.current_temp > (self.target_temp+self.error_integral_limit):
            self.error_integral = 0.0
        return self.error_integral

    ''' Set the debuglevel ''' 
    def debugLevel(self, val):
        self.debug = val

''' Subclass for Heater, this is an extruder '''
class Extruder(Heater):
    def __init__(self, smd, thermistor, mosfet):
        Heater.__init__(self, thermistor, mosfet, "Ext1")
        self.smd = smd
        self.enable()  


''' Subclass for heater, this is a Heated build platform '''
class HBP(Heater):
    def __init__(self, thermistor, mosfet):
        Heater.__init__(self, thermistor, mosfet, "HBP")
        self.enable()


