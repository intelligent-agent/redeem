
# Import PyBBIO library:
from bbio import *

''' Represents a thermistor'''
class Thermistor: 
	def __init__(self, pin):
		self.pin = pin
	
	''' Return the temperture in degrees celcius '''
	def getTemperature(self):		
  		val = analogRead(self.pin) # Get the ADC values:
		deg = self.valueToDegrees(val)
		return deg

	''' Need to implement this '''
	def valueToDegrees(self, value):
		return value
	
