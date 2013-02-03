#!/usr/bin/env python
'''
A fan is for blowing stuff away. This one is for Replicape. 

Author: Elias Bakken
email: elias.bakken@gmail.com
Website: http://www.hipstercircuits.com
License: BSD

You can use and change this, but keep this heading :)
'''

from Adafruit_I2C import Adafruit_I2C 
import time

PCA9685_MODE1 = 0x0
PCA9685_PRESCALE = 0xFE

pwm = Adafruit_I2C(0x70, 3, False) # Open device
pwm.write8(PCA9685_MODE1, 0x01)    # Reset 
time.sleep(0.05)				   # Wait for reset

class Fan:
	
	# Set the PWM frequency for all fans connected on this PWM-chip
	@staticmethod
	def setPWMFrequency(freq):
		prescaleval = 25000000
		prescaleval /= 4096;
		prescaleval /= float(freq);
		prescaleval -= 1;
		prescale = int(prescaleval + 0.5);

		oldmode = pwm.readU8(PCA9685_MODE1)
		newmode = (oldmode&0x7F) | 0x10
		pwm.write8(PCA9685_MODE1, newmode)  
		pwm.write8(PCA9685_PRESCALE, prescale)
		pwm.write8(PCA9685_MODE1, oldmode)
		time.sleep(0.05)
		pwm.write8(PCA9685_MODE1, oldmode | 0xA1)

	# Channel is the channel that the fan is on (0-7)
	def __init__(self, channel):
		self.channel = channel

	# Set the mount of "on"-time
	def setValue(self, value):
		off = min(1.0, value)
		off = int(value*4095)
		bytes = [0x00, 0x00, off & 0xFF, off >> 8]
		pwm.writeList(0x06+(4*self.channel), bytes)



