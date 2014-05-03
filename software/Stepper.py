#!/usr/bin/env python
'''
A Stepper Motor Driver class for Replicape. 

Author: Elias Bakken
email: elias(dot)bakken(at)gmail(dot)com
Website: http://www.thing-printer.com
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
'''

'''
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
'''

'''
The bits in the shift register are as follows (Rev A3):
D0 = DECAY   = X
D1 = MODE0   = X
D2 = MODE1   = X
D3 = MODE2 	 = X
D4 = nRESET  = 1
D5 = nSLEEP  = 1
D6 = nENABLE = 0
D7 = -   		 = X
'''

from threading import Thread
import time
import logging

try:
    from spi import SPI
    # init the SPI for the DAC
    spi2_0 = SPI(1, 0)	
    spi2_0.bpw = 8
    spi2_0.mode = 1
    # Init the SPI for the serial to parallel
    spi2_1 = SPI(1, 1)	
    spi2_1.bpw = 8
    spi2_1.mode = 0
except ImportError:
    pass

class Stepper:

    all_steppers = list()
    revision    = "A4"
    SLEEP       = 6
    ENABLED     = 4
    RESET       = 7
    DECAY       = 5
    
    ''' Send the values to the serial to parallel chips '''
    @staticmethod
    def commit():        
        bytes = []
        for stepper in Stepper.all_steppers:	   
            bytes.append(stepper.get_state())
        #txt = ", ".join([hex(b) for b in bytes[::-1]])
        #logging.debug("Updating steppers: "+txt)
        spi2_1.writebytes(bytes[::-1])

    ''' Init'''
    def __init__(self, stepPin, dirPin, faultPin, dac_channel, name, endstop, internalStepPin, internalDirPin):
        self.dac_channel     = dac_channel  # Which channel on the dac is connected to this stepper
        self.stepPin         = stepPin
        self.dirPin          = dirPin
        self.faultPin        = faultPin
        self.name            = name
        self.state           = (1<<Stepper.SLEEP)|(1<<Stepper.RESET)| (1<<Stepper.ENABLED) # The initial state of the inputs
        self.dacvalue 	     = 0x00   	    # The voltage value on the VREF		
        self.enabled 	     = False	      # Start disabled
        self.seconds_pr_step = 0.001        # Delay between each step (will be set by feed rate)
        self.steps_pr_mm     = 1            # Numer of steps pr mm. 
        self.microsteps      = 1.0          # Well, this is the microstep number
        self.pru_num         = -1           # PRU number, if any 
        self.direction       = 1
        self.endstop         = endstop
        self.internalStepPin = (1 << internalStepPin)
        self.internalDirPin = (1 << internalDirPin)
        Stepper.all_steppers.append(self)       # Add to list of steppers

    def get_endstop(self):
        return self.endstop

    ''' Sets the Stepper enabled '''
    def set_enabled(self, force_update=False):
        if not self.enabled:
            self.state &= ~(1<<Stepper.ENABLED)
            self.enabled = True
        if force_update: 
            self.update()
            	
    ''' Sets the Stepper disabled '''
    def set_disabled(self, force_update=False):
        if self.enabled:
            self.state |= (1<<Stepper.ENABLED)
            self.enabled = False
        if force_update: 
            self.update()

    '''Logic high to enable device, logic low to enter
    low-power sleep mode. Internal pulldown.'''
    def enable_sleepmode(self, force_update=False):
        self.state &= ~(1<<Stepper.SLEEP)		
        if force_update: 
            self.update()


    ''' Disables sleepmode (awake) '''
    def disable_sleepmode(self, force_update=False):
        self.state |= (1<<Stepper.SLEEP)		
        if force_update: 
            self.update()

    '''nReset - Active-low reset input initializes the indexer
    logic and disables the H-bridge outputs.
    Internal pulldown.'''
    def reset(self, force_update=False):
        self.state &= ~(1<<Stepper.RESET)
        self.update()
        time.sleep(0.001)
        self.state |= (1<<Stepper.RESET)
        self.update()

    ''' Microstepping (default = 0) 0 to 5 '''
    def set_microstepping(self, value, force_update=False):
        if not value in [0, 1, 2, 3, 4, 5]: # Full, half, 1/4, 1/8, 1/16, 1/32. 
            logging.warning("Tried to set illegal microstepping value: {0} for stepper {1}".format(value, self.name))
            return
        self.microsteps  = 2**value     # 2^val
        if Stepper.revision == "A4":
            # Keep bit 4, 5, 6, 7 intact but replace and reverse bit 1, 2, 3
            self.state = int("0b"+bin(self.state)[2:].rjust(8, '0')[:4]+bin(value)[2:].rjust(3, '0')[::-1]+"0", 2)
        else:
            # Keep bit 0, 4, 5, 6 intact but replace bit 1, 2, 3
            self.state = int("0b"+bin(self.state)[2:].rjust(8, '0')[:4]+bin(value)[2:].rjust(3, '0')+bin(self.state)[-1:], 2)
            #self.state = int("0b"+bin(self.state)[2:].rjust(8, '0')[:4]+bin(value)[2:].rjust(3, '0')+"0", 2)
        self.mmPrStep    = 1.0/(self.steps_pr_mm*self.microsteps)
        if force_update: 
            self.update()

    def set_decay(self, value, force_update=False):
        ''' Decay mode, look in the data sheet '''
        self.state &= ~(1<<Stepper.DECAY)        # bit 5 
        self.state |= (value<<Stepper.DECAY) 
        if force_update: 
            self.update()

    ''' Current chopping limit (This is the value you can change) '''
    def set_current_value(self, iChop):        
        vRef = 3.3                              # Voltage reference on the DAC
        rSense = 0.1                            # Resistance for the 
        vOut = iChop*5.0*rSense                 # Calculated voltage out from the DAC 

        self.dacval = int((vOut*256.0)/vRef)
        byte1 = ((self.dacval & 0xF0)>>4) | (self.dac_channel<<4)
        byte2 = (self.dacval & 0x0F)<<4
        spi2_0.writebytes([byte1, byte2])       # Update all channels
        spi2_0.writebytes([0xA0, 0xFF])         # TODO: Change to only this channel (1<<dac_channel) ?


    ''' Returns the current state '''
    def get_state(self):
        return self.state & 0xFF				# Return the state of the serial to parallel

    ''' Commits the changes	'''
    def update(self):
        Stepper.commit()						# Commit the serial to parallel

    '''
    Higher level commands 
    '''

    ''' Set the feed rate in mm/min '''
    def set_feed_rate(self, feed_rate):
        minutes_pr_mm = 1.0/float(feed_rate)
        seconds_pr_mm = minutes_pr_mm*60.0
        self.seconds_pr_step = self.mmPrStep*seconds_pr_mm
			
    ''' Sets the number of mm the stepper moves pr step. 
        This must be measured and calibrated '''
    def _setMMPrstep(self, mmPrStep):
        self.mmPrStep = mmPrStep

    ''' Set the number of steps pr mm. '''          
    def set_steps_pr_mm(self, steps_pr_mm):
        self.steps_pr_mm = steps_pr_mm
        self.mmPrStep = 1.0/(steps_pr_mm*self.microsteps)
    
    ''' Well, you can only guess what this function does. '''
    def set_max_feed_rate(self, max_feed_rate):
        self.max_feed_rate = max_feed_rate

    ''' Get the number of steps pr meter '''
    def get_steps_pr_meter(self):
        return self.steps_pr_mm*self.microsteps*1000.0

    ''' The pin that steps, it looks like GPIO1_31 aso '''
    def get_step_pin(self):
        return self.internalStepPin
    
    ''' Get the dir pin shifted into position '''
    def get_dir_pin(self):
        return self.internalDirPin

    def get_direction(self):
        return self.direction



