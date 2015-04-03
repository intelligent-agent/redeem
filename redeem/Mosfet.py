#!/usr/bin/env python
"""
A Mosfet class for setting the PWM of a power mosfet for Replicape.

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

PCA9685_MODE1 = 0x0
PCA9685_PRESCALE = 0xFE


# Looks like the interface has changed..
kernel_version = subprocess.check_output(["uname", "-r"]).strip()
[major, minor, rev] = kernel_version.split("-")[0].split(".")
if (int(major) == 3 and int(minor) >= 14) or int(major) > 3 :
    pwm = Adafruit_I2C(0x70, 2, False) # Open device
else:
    pwm = Adafruit_I2C(0x70, 1, False) # Open device

pwm.write8(PCA9685_MODE1, 0x01)    # Reset 
time.sleep(0.05)                   # Wait for reset


class Mosfet:
    # Set the PWM frequency for all fans connected on this PWM-chip
    @staticmethod
    def set_pwm_frequency(freq):
        prescaleval = 25000000
        prescaleval /= 4096
        prescaleval /= float(freq)
        prescaleval -= 1
        prescale = int(prescaleval + 0.5)

        oldmode = pwm.readU8(PCA9685_MODE1)
        newmode = (oldmode & 0x7F) | 0x10
        pwm.write8(PCA9685_MODE1, newmode)
        pwm.write8(PCA9685_PRESCALE, prescale)
        pwm.write8(PCA9685_MODE1, oldmode)
        time.sleep(0.05)
        pwm.write8(PCA9685_MODE1, oldmode | 0xA1)

    def __init__(self, channel):
        """ Channel is the channel that the thing is on (0-15) """
        self.channel = channel

    def set_power(self, value):
        """Set duty cycle between 0 and 1"""
        self.power = value
        off = min(1.0, value)
        off = int(value * 4095)
        bytes = [0x00, 0x00, off & 0xFF, off >> 8]
        pwm.writeList(0x06 + (4 * self.channel), bytes)

    def get_power(self):
        """ return the current power level """
        return self.power
