

import bbio as io
from threading import Thread

''' 
A heater element that must keep temperature, 
either an extruder, a HBP or could even be a heated chamer
'''
class Heater(object):
    ''' Init '''
    def __init__(self, thermistor, mosfet, name):
        self.thermistor = thermistor
        self.mosfet = mosfet
        self.name = name
        self.target_temp = 0 # Start off
        self.debug = 0

    ''' Set the desired temperature of the extruder '''
    def setTargetTemperature(self, temp):
        self.target_temp = temp

    ''' get the temperature of the thermistor'''
    def getTemperature(self):
        return self.thermistor.getTemperature()

    ''' Stops the heater and the PID controller '''
    def disable(self):
        self.enabled = False
        # Wait for PID to stop
        while self.disabled == False:
            io.delay(200)
        # The PID loop has finished		
        self.mosfet.setPower(0)

    ''' Start the PID controller '''
    def enable(self):
        self.enabled = True
        self.disabled = False
        self.t = Thread(target=self.keep_temperature)
        self.t.start()		

    ''' Set values for Proportional, Integral, Derivative'''
    def setPIDvalues(self, P, I, D):
        self.P = P # Proportional 
        self.I = I
        self.D = D

    ''' PID Thread that keeps the temperature stable '''
    def keep_temperature(self):
        while self.enabled:
            # Read the current temperature					
            self.current_temp = self.getTemperature()
            # Calculate the error 
            error = self.target_temp-self.current_temp            
            # The formula for the PID
            power = self.P*error
            # Normalize to 0,1
            power = max(min(power, 1.0), 0.0)
            # Update the mosfet
            self.mosfet.setPower(power)
            # Debug if necessary 
            if self.debug > 0:
                print self.name+": Target: %f, Current: %f, error: %f, power: %f"%(self.target_temp, self.current_temp, error, power)
            # Wait one second
            io.delay(1000)

        # Signal the disable that we are done
        self.disabled = True

    # 
    def debugLevel(self, val):
        self.debug = val

''' Subclass for Heater, this is an extruder '''
class Extruder(Heater):
    def __init__(self, smd, thermistor, mosfet):
        Heater.__init__(self, thermistor, mosfet, "Ext1")
        self.smd = smd
        self.enable()
        # Should be read from file
        self.setPIDvalues(P=0.01, I=0, D=0)

''' Subclass for heater, this is a Heated build platform '''
class HBP(Heater):
    def __init__(self, thermistor, mosfet):
        Heater.__init__(self, thermistor, mosfet, "HBP")
        self.enable()
        # Should be read from file
        self.setPIDvalues(P=0.05, I=0, D=0)

	

