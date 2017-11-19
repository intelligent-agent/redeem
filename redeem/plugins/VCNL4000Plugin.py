"""
Plugin for VCNL4000 IR proximity sensor from Adafruit

Author: Elias Bakken
email:
Website:
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


class VCNL4000(object):

    def __init__(self):
        kernel_version = subprocess.check_output(["uname", "-r"]).strip()
        [major, minor, rev] = kernel_version.split("-")[0].split(".")
        if (int(major) == 3 and int(minor) >= 14) or int(major) > 3 :
            self.i2c = Adafruit_I2C(0x13, 2, False)  # Open device
        else:
            self.i2c = Adafruit_I2C(0x13, 1, False)  # Open device
        rev = self.i2c.readU8(0x81)
        if rev == 0x11:
            logging.info("Found VCNL4000")
        else:
            logging.warning("VCNL4000 error, found revision number "+str(rev))
        self.i2c.write8(0x84, 0x0F)
        self.i2c.write8(0x83, 20) 
        self.i2c.write8(0x89, 2)
        self.i2c.write8(0x8A, 0x81)

    def get_distance(self):
        val = 0
        i = 0
        state = self.i2c.readU8(0x80)
        print(state)
        self.i2c.write8(0x80, (1<<3))
        while True:
            state = self.i2c.readU8(0x80)
            print(state)
            if (state & (1 << 5)) or i > 100:
                val |= (self.i2c.readU8(0x87) << 8)
                val |= (self.i2c.readU8(0x88) << 0)
                return val
            i += 1
            time.sleep(0.01)
        return val

    def get_ambient(self):
        val = 0
        i = 0
        self.i2c.write8(0x80, (1<<4))
        while True:
            state = self.i2c.readU8(0x80)
            if (state & (1 << 6)) or i > 100:
                val |= (self.i2c.readU8(0x85) << 8)
                val |= (self.i2c.readU8(0x86) << 0)
                return val
            i += 1
            time.sleep(0.01)
        return val

if __name__ == '__main__':
    import os
    import logging
    import numpy as np

    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%m-%d %H:%M')

    prox = VCNL4000()
    for i in range(100):
        print(prox.get_distance())
        #print(prox.get_ambient())
        #time.sleep(0.1)
