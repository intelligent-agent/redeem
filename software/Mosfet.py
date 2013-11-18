#!/usr/bin/env python
'''
A Mosfet class for setting the PWM of a power mosfet for Replicape. 

Author: Elias Bakken
email: elias(dot)bakken(at)gmail(dot)com
Website: http://www.thing-printer.com
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
'''

from Adafruit_I2C import Adafruit_I2C 
import time

PCA9685_MODE1 = 0x0
PCA9685_PRESCALE = 0xFE
DEVICE_TREE = True

pwm = Adafruit_I2C(0x70, 1, False) # Open device

pwm.write8(PCA9685_MODE1, 0x01)    # Reset 
time.sleep(0.05)				   # Wait for reset 

class Mosfet:
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

    # Channel is the channel that the thing is on (0-15)
    def __init__(self, channel):
        self.channel = channel
	
    '''Set duty cycle between 0 and 1'''
    def setPower(self, value):
        self.power = value
        off = min(1.0, value)
        off = int(value*4095)
        bytes = [0x00, 0x00, off & 0xFF, off >> 8]
        pwm.writeList(0x06+(4*self.channel), bytes)
   
    ''' return the current power level '''
    def get_power(self):
        return self.power

