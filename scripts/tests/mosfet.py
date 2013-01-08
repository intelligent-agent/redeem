from bbio import *

ext1 = PWM1A

class MOSFET:

	def __init__(self):
		pwmEnable(ext1) # Init the Pin to PWM mode
		pwmFrequency(ext1, 1000) # Set a frequency, not important for now

	'''Set duty cycle between 0 and 1'''
	def setValue(self, value):
		analogWrite(ext1, int(value*255.0))

	'''Set the PWM frequency'''
	def setFrequency(self, freq):
		pwmFrequency(ext1, freq)

