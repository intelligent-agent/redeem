#!/usr/bin/env python
"""
A Stepper Motor Driver class for Replicape.

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

import time
import logging
from Path import Path
from DAC import DAC, PWM_DAC
from ShiftRegister import ShiftRegister


class Stepper(object):

    all_steppers = list()
    
    def __init__(self, stepPin, dirPin, faultPin, dac_channel, shiftreg_nr, name, internalStepPin, internalDirPin):
        """ Init """
        self.dac_channel     = dac_channel  # Which channel on the dac is connected to this stepper
        self.stepPin         = stepPin
        self.dirPin          = dirPin
        self.faultPin        = faultPin
        self.name            = name
        self.enabled 	     = False	    
        self.in_use          = False        
        self.steps_pr_mm     = 1            
        self.microsteps      = 1.0          
        self.direction       = 1
        self.internalStepPin = (1 << internalStepPin)
        self.internalDirPin  = (1 << internalDirPin)

        # Set up the Shift register
        ShiftRegister.make()
        self.shift_reg = ShiftRegister.registers[shiftreg_nr]

    def get_state(self):
        """ Returns the current state """
        return self.state & 0xFF  # Return the state of the serial to parallel

    def update(self):
        """ Commits the changes	"""
        ShiftRegister.commit()  # Commit the serial to parallel

    # Higher level commands
    def set_steps_pr_mm(self, steps_pr_mm):
        """ Set the number of steps pr mm. """
        self.steps_pr_mm = steps_pr_mm
        self.mmPrStep = 1.0 / (steps_pr_mm * self.microsteps)
    
    def get_steps_pr_meter(self):
        """ Get the number of steps pr meter """
        return self.steps_pr_mm*self.microsteps * 1000.0

    def get_step_pin(self):
        """ The pin that steps, it looks like GPIO1_31 aso """
        return self.internalStepPin
    
    def get_dir_pin(self):
        """ Get the dir pin shifted into position """
        return self.internalDirPin

    def get_direction(self):
        return self.direction

    @staticmethod
    def commit():
        pass



"""
The bits in the shift register are as follows (Rev B1): 
Bit - name   - init val 
D0 = -		 = X (or servo enable)
D1 = CFG5    = 0 (Chopper blank time)
D2 = CFG4    = 0 (Choppper hysteresis)
D3 = CFG0    = 0 (Chopper off time)
D4 = CFG2    = 0 (microstepping)
D5 = CFG2-Z  = 0 (microstepping)
D6 = CFG1    = 0 (microstepping)
D7 = CFG1-Z  = 0 (microstepping)
"""

class Stepper_00B1(Stepper):

    def __init__(self, stepPin, dirPin, faultPin, dac_channel, shiftreg_nr, name, internalStepPin, internalDirPin):
        Stepper.__init__(self, stepPin, dirPin, faultPin, dac_channel, shiftreg_nr, name, internalStepPin, internalDirPin)
        self.dac    = PWM_DAC(dac_channel)
        self.state  = 0 # The initial state of shift register

    def set_microstepping(self, value, force_update=False):                
        """ Todo: Find an elegant way for this """
        EN_CFG1  = (1<<7)
        DIS_CFG1 = (0<<7)
        EN_CFG2  = (1<<5)
        DIS_CFG2 = (0<<5)
        CFG2_H   = (1<<4)
        CFG2_L   = (0<<4)
        CFG1_H   = (1<<6)
        CFG1_L   = (0<<6)

        if   value == 0:   # GND, GND
            state = EN_CFG2 | CFG2_L | EN_CFG1 | CFG1_L
            self.microsteps = 1
        elif value == 1: # GND, VCC
            state = EN_CFG2 | CFG2_L | EN_CFG1 | CFG1_H
            self.microsteps = 2
        elif value == 2: # GND, open
            state = EN_CFG2 | CFG2_L | DIS_CFG1 | CFG1_L
            self.microsteps = 2
        elif value == 3: # VCC, GND
            state = EN_CFG2 | CFG2_H | EN_CFG1 | CFG1_L
            self.microsteps = 4
        elif value == 4: # VCC, VCC
            state = EN_CFG2 | CFG2_H | EN_CFG1 | CFG1_H
            self.microsteps = 16
        elif value == 5: # VCC, open
            state = EN_CFG2 | CFG2_H | DIS_CFG1 | CFG1_L
            self.microsteps = 4
        elif value == 6: # open, GND
            state = DIS_CFG2 | CFG2_L | EN_CFG1 | CFG1_L
            self.microsteps = 16
        elif value == 7: # open, VCC
            state = DIS_CFG2 | CFG2_L | EN_CFG1 | CFG1_H
            self.microsteps = 4
        elif value == 8: # open, open
            state = DIS_CFG2 | CFG2_L | DIS_CFG1 | CFG1_L
            self.microsteps = 16

        self.shift_reg.set_state(state,0xF0)
        self.mmPrStep    = 1.0/(self.steps_pr_mm*self.microsteps)

        # update the Path class with new values
        stepper_num = Path.axis_to_index(self.name)
        Path.steps_pr_meter[stepper_num] = self.get_steps_pr_meter()
        logging.debug("Updated stepper "+self.name+" to microstepping "+str(value)+" = "+str(self.microsteps))   


    def set_current_value(self, i_rms):
        """ Current chopping limit (This is the value you can change) """
        self.current_value = i_rms
        
        r_sense = 0.1020              # External resistors + internal
        sqrt_2 = 1.41421356237

        v_iref = 2.5*(i_rms/1.92)
        if(v_iref > 2.5):
            logging.warning("Current ref for stepper "+self.name+" above limit (2.5 V). Setting to 2.5 V")
            v_iref = 2.5
        logging.debug("Setting votage to "+str(v_iref)+" for "+self.name)
        self.dac.set_voltage(v_iref)

    def set_disabled(self, force_update=False):
        if hasattr(Stepper, "printer"):
            Stepper.printer.enable.set_disabled()

    def set_enabled(self, force_update=False):
        if hasattr(Stepper, "printer"):
            Stepper.printer.enable.set_enabled()

    def set_decay(self, value):
        pass


class Stepper_00B2(Stepper_00B1):

    def __init__(self, stepPin, dirPin, faultPin, dac_channel, shiftreg_nr, name, internalStepPin, internalDirPin):
        Stepper_00B1.__init__(self, stepPin, dirPin, faultPin, dac_channel, shiftreg_nr, name, internalStepPin, internalDirPin)
        self.dac    = PWM_DAC(dac_channel)
        self.state  = 0 # The initial state of shift register
    
    def set_disabled(self, force_update=False):
        if not self.enabled:
            return
        logging.debug("Disabling stepper "+self.name)
        # X, Y, Z steppers are on the first shift reg. Extruders have their own.  
        if self.name in ["X", "Y", "Z"]:
            ShiftRegister.registers[0].add_state(0x1)
        elif self.name == "E":
            ShiftRegister.registers[3].add_state(0x1)
        elif self.name == "H":
            ShiftRegister.registers[4].add_state(0x1)
        self.enabled = False

    def set_enabled(self, force_update=False):
        if self.enabled:
            return
        logging.debug("Enabling stepper "+self.name)
        # X, Y, Z steppers are on the first shift reg. Extruders have their own.  
        if self.name in ["X", "Y", "Z"]:
            ShiftRegister.registers[0].remove_state(0x1) # First bit low. 
        elif self.name == "E":
            ShiftRegister.registers[3].remove_state(0x1)
        elif self.name == "H":
            ShiftRegister.registers[4].remove_state(0x1)
        self.enabled = True

"""
The bits in the shift register are as follows (Rev A4) :
Bit - name   - init val 
D0 = -		   = X
D1 = MODE2   = 0
D2 = MODE1   = 0
D3 = MODE0   = 0
D4 = nENABLE = 0  - Enabled
D5 = DECAY   = 0  - Slow decay 
D6 = nSLEEP  = 1  - Not sleeping 
D7 = nRESET  = 1  - Not in reset mode
"""

class Stepper_00A4(Stepper):
    revision    = "A4"
    SLEEP       = 6
    ENABLED     = 4
    RESET       = 7
    DECAY       = 5

    def __init__(self, stepPin, dirPin, faultPin, dac_channel, shiftreg_nr, name, internalStepPin, internalDirPin):
        Stepper.__init__(self, stepPin, dirPin, faultPin, dac_channel, shiftreg_nr, name, internalStepPin, internalDirPin)
        self.dac        = DAC(dac_channel)
        self.dacvalue 	= 0x00   	    # The voltage value on the VREF		
        self.state      = (1<<Stepper_00A4.SLEEP)|(1<<Stepper_00A4.RESET)| (1<<Stepper_00A4.ENABLED) # The initial state of the inputs
        self.update()

    def set_enabled(self, force_update=False):
        """ Sets the Stepper enabled """
        if not self.enabled:
            self.state &= ~(1 << Stepper_00A4.ENABLED)
            self.enabled = True
        self.update()

    def set_disabled(self, force_update=False):
        """ Sets the Stepper disabled """
        if self.enabled:
            self.state |= (1 << Stepper_00A4.ENABLED)
            self.enabled = False
        self.update()

    def enable_sleepmode(self, force_update=False):
        """Logic high to enable device, logic low to enter
        low-power sleep mode. Internal pulldown."""
        self.state &= ~(1 << Stepper_00A4.SLEEP)
        self.update()

    def disable_sleepmode(self, force_update=False):
        """ Disables sleepmode (awake) """
        self.state |= (1<<Stepper_00A4.SLEEP)
        self.update()

    def reset(self, force_update=False):
        """nReset - Active-low reset input initializes the indexer
        logic and disables the H-bridge outputs.
        Internal pulldown."""
        self.state &= ~(1 << Stepper_00A4.RESET)
        self.update()
        time.sleep(0.001)
        self.state |= (1 << Stepper_00A4.RESET)
        self.update()
    
    def set_microstepping(self, value, force_update=False):        
        """ Microstepping (default = 0) 0 to 5 """        
        if not value in [0, 1, 2, 3, 4, 5]: # Full, half, 1/4, 1/8, 1/16, 1/32.
            logging.warning("Tried to set illegal microstepping value: {0} for stepper {1}".format(value, self.name))
            return
        self.microstepping = value
        self.microsteps  = 2**value     # 2^val
        # Keep bit 0, 4, 5, 6 intact but replace bit 1, 2, 3
        self.state = int("0b"+bin(self.state)[2:].rjust(8, '0')[:4]+bin(value)[2:].rjust(3, '0')[::-1]+"0", 2)
        #self.state = int("0b"+bin(self.state)[2:].rjust(8, '0')[:4]+bin(value)[2:].rjust(3, '0')+bin(self.state)[-1:], 2)
        self.mmPrStep    = 1.0/(self.steps_pr_mm*self.microsteps)

        # update the Path class with new values
        stepper_num = Path.axis_to_index(self.name)
        Path.steps_pr_meter[stepper_num] = self.get_steps_pr_meter()
        self.update()

    def set_current_value(self, iChop):
        """ Current chopping limit (This is the value you can change) """
        self.current_value = iChop
        rSense = 0.1                  # Resistance for the
        v_out = iChop * 5.0 * rSense  # Calculated voltage out from the DAC
        self.dac.set_voltage(v_out)

    def set_decay(self, value, force_update=False):
        """ Decay mode, look in the data sheet """
        self.decay = value
        self.state &= ~(1 << Stepper_00A4.DECAY)        # bit 5
        self.state |= (value << Stepper_00A4.DECAY)
        self.update()

    def update(self):
        # Invert shizzle
        self.shift_reg.set_state(self.state)    
        #logging.debug("Updated stepper {} to enabled, state: {}".format(self.name, bin(self.state)))


"""
The bits in the shift register are as follows (Rev A3):
D0 = DECAY   = X
D1 = MODE0   = X
D2 = MODE1   = X
D3 = MODE2 	 = X
D4 = nRESET  = 1
D5 = nSLEEP  = 1
D6 = nENABLE = 0
D7 = -   		 = X
"""

class Stepper_00A3(Stepper_00A4):
    Stepper.revision = "A3"
    Stepper.ENABLED = 6
    Stepper.SLEEP = 5
    Stepper.RESET = 4
    Stepper.DECAY = 0

