#!/usr/bin/env python
"""
A fan is for blowing stuff away. This one is for Replicape.

Author: Elias Bakken
email: elias(dot)bakken(at)gmail(dot)com
Website: http://www.thing-printer.com
License: GNU GPL v3: http://www.gnu.org/copyleft/gpl.html

 Redeem is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 Redeem is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with Redeem.  If not, see <http://www.gnu.org/licenses/>.
"""

from Adafruit_I2C import Adafruit_I2C 
import time
import subprocess


class Fan(object):

    pwm_frequency = 0
    pwm = None

    PCA9685_MODE1 = 0x0
    PCA9685_PRESCALE = 0xFE

    @staticmethod
    def __init_pwm():
        kernel_version = subprocess.check_output(["uname", "-r"]).strip()
        if kernel_version == "3.14.14":
            Fan.pwm = Adafruit_I2C(0x70, 2, False)  # Open device
        else:
            Fan.pwm = Adafruit_I2C(0x70, 1, False)  # Open device
        Fan.pwm.write8(Fan.PCA9685_MODE1, 0x01)    # Reset
        time.sleep(0.05)                   # Wait for reset

    @staticmethod
    def set_PWM_frequency(freq):
        """ Set the PWM frequency for all fans connected on this PWM-chip """

        if Fan.pwm is None:
            Fan.__init_pwm()

        prescaleval = 25000000
        prescaleval /= 4096
        prescaleval /= float(freq)
        prescaleval -= 1
        prescale = int(prescaleval + 0.5)

        oldmode = Fan.pwm.readU8(Fan.PCA9685_MODE1)
        newmode = (oldmode & 0x7F) | 0x10
        Fan.pwm.write8(Fan.PCA9685_MODE1, newmode)
        Fan.pwm.write8(Fan.PCA9685_PRESCALE, prescale)
        Fan.pwm.write8(Fan.PCA9685_MODE1, oldmode)
        time.sleep(0.05)
        Fan.pwm.write8(Fan.PCA9685_MODE1, oldmode | 0xA1)

        Fan.pwm_frequency = freq

    @staticmethod
    def get_PWM_frequency(freq):
        return Fan.pwm_frequency

    def __init__(self, channel):
        """ Channel is the channel that the fan is on (0-7) """

        if Fan.pwm is None:
            Fan.__init_pwm()
        
        self.channel = channel

    def set_value(self, value):
        """ Set the amount of on-time from 0..1 """
        #off = min(1.0, value)
        off = int(value*4095)
        byte_list = [0x00, 0x00, off & 0xFF, off >> 8]
        Fan.pwm.writeList(0x06+(4*self.channel), byte_list)
