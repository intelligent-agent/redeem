#!/usr/bin/env python
"""
This is an implementation of the PWM DAC

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


class PWM(object):

    frequency = 0
    i2c = None

    PCA9685_MODE1 = 0x0
    PCA9685_PRESCALE = 0xFE

    @staticmethod
    def __init_pwm():
        kernel_version = subprocess.check_output(["uname", "-r"]).strip()
        [major, minor, rev] = kernel_version.split("-")[0].split(".")
        if (int(major) == 3 and int(minor) >= 14) or int(major) > 3 :
            PWM.i2c = Adafruit_I2C(0x70, 2, False)  # Open device
        else:
            PWM.i2c = Adafruit_I2C(0x70, 1, False)  # Open device
        PWM.i2c.write8(PWM.PCA9685_MODE1, 0x01)    # Reset


    @staticmethod
    def set_frequency(freq):
        """ Set the PWM frequency for all fans connected on this PWM-chip """

        if PWM.i2c is None:
            PWM.__init_pwm()
        prescaleval = 25000000
        prescaleval /= 4096
        prescaleval /= float(freq)
        prescaleval = int(prescaleval + 0.5)
        prescaleval -= 1

        oldmode = PWM.i2c.readU8(PWM.PCA9685_MODE1)
        newmode = (oldmode & 0x7F) | 0x10
        PWM.i2c.write8(PWM.PCA9685_MODE1, newmode)
        PWM.i2c.write8(PWM.PCA9685_PRESCALE, prescaleval)
        PWM.i2c.write8(PWM.PCA9685_MODE1, oldmode)
        time.sleep(0.05)
        PWM.i2c.write8(PWM.PCA9685_MODE1, oldmode | 0xA1)

        PWM.frequency = freq

    @staticmethod
    def set_value(value, channel):
        """ Set the amount of on-time from 0..1 """
        off = int(value*4095)
        byte_list = [0x00, 0x00, off & 0xFF, off >> 8]
        PWM.i2c.writeList(0x06+(4*channel), byte_list)

if __name__ == '__main__':
    import os
    import logging
    import numpy as np

    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%m-%d %H:%M')

    exp = 2.3   

    PWM.set_frequency(1000)
    while True:
        for i in np.linspace(0.0, 6.28, 100):
            logging.info((0.5+0.5*np.sin(i)))        
            PWM.set_value((0.5+0.5*np.sin(i+0.0*np.pi/2.0))**exp, 7)
            PWM.set_value((0.5+0.5*np.sin(i+1.0*np.pi/2.0))**exp, 8)
            PWM.set_value((0.5+0.5*np.sin(i+2.0*np.pi/2.0))**exp, 9)
            PWM.set_value((0.5+0.5*np.sin(i+3.0*np.pi/2.0))**exp, 10)
            time.sleep(0.01)


