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
try:
    from Adafruit_GPIO.I2C import Device as I2C
except: 
    pass
import time
import subprocess
import logging
import os

class PWM_PCA9685(object):

    frequency = 0
    i2c = None

    PCA9685_MODE1 = 0x0
    PCA9685_PRESCALE = 0xFE

    def __init__(self, channel):
        self.channel = channel
    
    def set_value(self, value):
        PWM_PCA9685.set_value(value, self.channel)

    @staticmethod
    def __init_pwm():
        kernel_version = subprocess.check_output(["uname", "-r"]).strip()
        [major, minor, rev] = kernel_version.split("-")[0].split(".")
        if (int(major) == 3 and int(minor) >= 14) or int(major) > 3 :
            PWM_PCA9685.i2c = I2C(0x70, 2)  # Open device
        else:
            PWM_PCA9685.i2c = I2C(0x70, 1)  # Open device
        PWM_PCA9685.i2c.write8(PWM.PCA9685_MODE1, 0x01)    # Reset


    @staticmethod
    def set_frequency(freq):
        """ Set the PWM frequency for all fans connected on this PWM-chip """

        if PWM_PCA9685.i2c is None:
            PWM_PCA9685.__init_pwm()
        prescaleval = 25000000
        prescaleval /= 4096
        prescaleval /= float(freq)
        prescaleval = int(prescaleval + 0.5)
        prescaleval -= 1

        oldmode = PWM.i2c.readU8(PWM.PCA9685_MODE1)
        newmode = (oldmode & 0x7F) | 0x10
        PWM_PCA9685.i2c.write8(PWM.PCA9685_MODE1, newmode)
        PWM_PCA9685.i2c.write8(PWM.PCA9685_PRESCALE, prescaleval)
        PWM_PCA9685.i2c.write8(PWM.PCA9685_MODE1, oldmode)
        time.sleep(0.05)
        PWM_PCA9685.i2c.write8(PWM.PCA9685_MODE1, oldmode | 0xA1)

        PWM_PCA9685.frequency = freq

    @staticmethod
    def set_value(value, channel):
        """ Set the amount of on-time from 0..1 """
        off = int(value*4095)
        byte_list = [0x00, 0x00, off & 0xFF, off >> 8]
        PWM_PCA9685 .i2c.writeList(0x06+(4*channel), byte_list)



class PWM_AM335(object):
    def __init__(self, pin, frequency, duty_cycle): 

        self.enabled = False
        if pin == "P9_14":
            self.chip = 0
            self.channel = 0
        elif pin == "P9_16":
            self.chip = 0
            self.channel = 1
        elif pin == "0:0":
            self.chip = 0
            self.channel = 0
        elif pin == "0:1":
            self.chip = 0
            self.channel = 1
        elif pin == "2:0":
            self.chip = 2
            self.channel = 0
        elif pin == "2:1":
            self.chip = 2
            self.channel = 1
        elif pin == "4:0":
            self.chip = 4
            self.channel = 0
        elif pin == "5:0":
            self.chip = 5
            self.channel = 0
        elif pin == "6:0":
            self.chip = 6
            self.channel = 0
        elif pin == "7:0":
            self.chip = 7
            self.channel = 0
        else:
            logging.error("PWM_AM335: Unrecognized pin '{}'. You may have to implement it...".format(pin))
            return

        self.export_chip(self.chip, self.channel)
        self.set_frequency(frequency)
        self.set_value(duty_cycle)
        
    def export_chip(self, chip, channel):
        self.base = "/sys/class/pwm/pwmchip{}/pwm-{}:{}".format(chip, chip, channel)
        if not os.path.exists(self.base):
            with open("/sys/class/pwm/pwmchip{}/export".format(chip), "w") as f:
                f.write(str(channel))
            if not os.path.exists(self.base):
                logging.warning("Unable to export PWM pin")
        

    def set_enabled(self, is_enabled = True):
        if self.enabled == is_enabled:
            return
        path = self.base+"/enable"
        with open(path, "w") as f:           
            f.write("1" if is_enabled else "0")
        self.enabled = is_enabled


    def set_frequency(self, freq):
        """ Set the PWM frequency for all fans connected on this PWM-chip """
        # period is specified in picoseconds
        period = int( (1.0/float(freq))*(10**9) )
        self.period = period
        path = self.base+"/period"
        logging.debug("Setting period to "+str(period))
        with open(path, "w") as f:
            f.write(str(period))

    def set_value(self, value):
        """ Set the amount of on-time from 0..1 """
        duty_cycle = int(self.period*float(value))
        path = self.base+"/duty_cycle"
        #logging.debug("Setting duty_cycle to "+str(duty_cycle))
        with open(path, "w") as f:
            f.write(str(duty_cycle))
        # Call enable/disable here since the timer pins 
        self.set_enabled( (value > 0) )


    def ramp_to(self, value, delay=0.01):
        ''' Set the fan/light value to the given value, in degree, with the given speed in deg / sec '''
        for w in xrange(int(self.value*255.0), int(value*255.0), (1 if value>=self.value else -1)):
            self.set_value(w/255.0)
            time.sleep(delay)
        self.set_value(value)


if __name__ == '__main__':
   
    # This is now broken!

    p1 = PWM_AM335("P9_14", 50, 0.1)
    p2 = PWM_AM335("P9_16", 50, 0.1)
    
    while 1:
        for i in range(100):
            p1.set_value(0.1+(i*0.001))
            p2.set_value(0.1+(i*0.001))
            time.sleep(0.03)
        for i in range(100):
            p1.set_value(0.2-(i*0.001))
            p2.set_value(0.2-(i*0.001))
            time.sleep(0.03)

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


