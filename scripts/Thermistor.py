
# Import PyBBIO library:
import bbio as io
import numpy as np

# Import the temp chart. 
from temp_chart import *

 
''' Represents a thermistor'''
class Thermistor: 
	def __init__(self, pin, name, chart_name="B57560G104F"):
		self.pin = pin
		self.name = name
		# Get the chart and transpose it
		self.temp_table = map(list, zip(*temp_chart[chart_name]))    

		self.debug = 0
	
	''' Return the temperture in degrees celcius '''
	def getTemperature(self):	
		adc_val = io.analogRead(self.pin)
		#for i in range(100):
		#	adc_val+= io.analogRead(self.pin)
		#adc_val /= 100.0	
		voltage = io.inVolts(adc_val)                 # Convert to voltage
		res_val = self.voltage_to_resistance(voltage)    # Convert to resistance  
		temperature = self.resistance_to_degrees(res_val) # Convert to degrees
		if self.debug > 1:  
			print self.name+": ADC: %i - voltage: %fv - thermistor res: %f - Temperature: %f deg." % (adc_val, voltage, res_val, temperature)
    
		return temperature

	''' Need to implement this '''
	def valueToDegrees(self, value):
		return value
	
	# Return the temperature nearest to the resistor value
	def resistance_to_degrees(self, resistor_val):
	    idx = (np.abs(np.array(self.temp_table[1])-resistor_val)).argmin()
	    return self.temp_table[0][idx]

	# Convert the voltage to a resistance value
	def voltage_to_resistance(self, v_sense):
	    return  4700.0/((1.8/v_sense)-1.0)

	# Set the deuglevel
	def setDebugLevel(self, val):
		self.debug = val

