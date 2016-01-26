#!/usr/bin/env python
"""
Implements an 8 bit shift register controlled via SPI. 

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

spi = None

# Load SPI module
try:
    from Adafruit_BBIO.SPI import SPI
except ImportError:
    pass

if 'SPI' in globals():
    # Init the SPI for the serial to parallel
    try:
        spi = SPI(1, 1)
    except:
        pass
    spi.bpw = 8
    spi.mode = 0
else:
    logging.warning("Unable to set up SPI")
    spi = None

class ShiftRegister(object):

    registers = list()
    
    @staticmethod
    def commit():
        """ Send the values to the serial to parallel chips """
        if spi is None:
            return
        
        bytes = []
        for reg in ShiftRegister.registers:
            bytes.append(reg.state)
        spi.writebytes(bytes[::-1])

    @staticmethod
    def make():
        if len(ShiftRegister.registers) == 0:
            for i in range(5):
                ShiftRegister()

    def __init__(self):
        """ Init """
        ShiftRegister.registers.append(self)       # Add to list of steppers    
        self.state = 0x00

    def set_state(self, state, mask=0xFF):
        self.remove_state(mask)
        self.state = state & mask
        ShiftRegister.commit()

    def add_state(self, state):
        self.state |= state
        ShiftRegister.commit()

    def remove_state(self, state):
        self.state &= ~state
        ShiftRegister.commit()
    

if __name__ == '__main__':

    ShiftRegister.make()
    reg2 = ShiftRegister.registers[2]
    reg3 = ShiftRegister.registers[3]
    reg2.add_state( 0x01 )
    reg3.add_state( 0x01 )


