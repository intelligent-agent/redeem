#!/usr/bin/python
''' 
Replicape main program
'''

from bbio import *

from Heater import Heater
from Smd import SMD
from Thermistor import Thermistor
from Fan import Fan

class Replicape:

	def __init__(self):

		# init the 5 Stepper motors
		self.smd_x = SMD(GPIO1_12, GPIO1_13, GPIO1_7, 7)  # Fault_x should be PWM2A?

		# init the 3 thermistors
		self.therm_ext1 = Thermistor(AIN4)
		self.therm_ext2 = Thermistor(AIN5)
		self.therm_hbp  = Thermistor(AIN6)

		# init the 3 heaters
		self.heater_ext1 = Heater(PWM1A) 

		# Init the three fans
		self.fan_1 = Fan(1)
		self.fan_2 = Fan(2)
		self.fan_3 = Fan(3)


	# Test some shit
	def test(self):
		self.smd_x.setCurrentValue(2.0) # 2A
		self.smd_x.setEnabled()
		self.smd_x.step(1000)
		

	def step(self, delay):
		self.smd_x.setDelay(delay)
		self.smd_x.step(1000)
		


