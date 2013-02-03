#!/usr/bin/env python
'''
A Mosfet class for setting the PWM of a power mosfet for Replicape. 

Author: Elias Bakken
email: elias.bakken@gmail.com
Website: http://www.hipstercircuits.com
License: BSD

You can use and change this, but keep this heading :)
'''
import bbio as io

class Mosfet:

	def __init__(self, pin):
		self.pin = pin
		io.pwmEnable(pin) # Init the Pin to PWM mode
		io.pwmFrequency(pin, 20000) # Set a frequency, not important for now
		self.power = 0.0		
		
	'''Set duty cycle between 0 and 1'''
	def setPower(self, value):
		self.power = value
		io.analogWrite(self.pin, int(value*256.0))

	'''Set the PWM frequency'''
	def setFrequency(self, freq):
		io.pwmFrequency(self.pin, freq)

	''' return the current power level '''
	def get_power(self):
		return self.power
