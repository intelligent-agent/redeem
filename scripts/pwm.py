#!/usr/bin/python 

'''
***************************************************
This is a library for our Adafruit 16-channel PWM & Servo driver

Pick one up today in the adafruit shop!
------> http://www.adafruit.com/products/815

These displays use I2C to communicate, 2 pins are required to
interface. For Arduino UNOs, thats SCL -> Analog 5, SDA -> Analog 4

Adafruit invests time and resources providing this open source code,
please support Adafruit and open-source hardware by purchasing
products from Adafruit!

Written by Limor Fried/Ladyada for Adafruit Industries.
BSD license, all text above must be included in any redistribution
****************************************************

This code was loosly based on the Adafruit PCA9685 library, which was for 
Arduino. I guess credit must be given to Adafruit for this : )
'''


from Adafruit_I2C import Adafruit_I2C 
import time

PCA9685_MODE1 = 0x0
PCA9685_PRESCALE = 0xFE

class PWM:

	def __init__(self):
		self.pwm = Adafruit_I2C(0x70, 3, False)
		# reset
		self.pwm.write8(PCA9685_MODE1, 0x01)  
		time.sleep(0.05)

	def setFrequency(self, freq):
		prescaleval = 25000000
		prescaleval /= 4096;
		prescaleval /= float(freq);
		prescaleval -= 1;
		prescale = int(prescaleval + 0.5);

		oldmode = self.pwm.readU8(PCA9685_MODE1)
		newmode = (oldmode&0x7F) | 0x10
		self.pwm.write8(PCA9685_MODE1, newmode)  
		self.pwm.write8(PCA9685_PRESCALE, prescale)
		self.pwm.write8(PCA9685_MODE1, oldmode)
		time.sleep(0.05)
		self.pwm.write8(PCA9685_MODE1, oldmode | 0xA1)


	def setDutyCycle(self, channel, cycle):
		off = min(1, cycle)
		off = int(cycle*4095)
		bytes = [0x00, 0x00, off & 0xFF, off >> 8]
		self.pwm.writeList(0x06+(4*channel), bytes)
		

