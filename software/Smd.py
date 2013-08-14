#!/usr/bin/env python
'''
A Stepper Motor Driver class for Replicape. 

Author: Elias Bakken
email: elias.bakken@gmail.com
Website: http://www.hipstercircuits.com
License: BSD

You can use and change this, but keep this heading :)
'''

'''
The bits in the shift register are as follows:
D0 = DECAY   = X
D1 = MODE0   = X
D2 = MODE1   = X
D3 = MODE2 	 = X
D4 = nRESET  = 1
D5 = nSLEEP  = 1
D6 = nENABLE = 0
D7 = 		 = 0
'''
from spi import SPI
from threading import Thread
import time
import logging

# init the SPI for the DAC
spi2_0 = SPI(1, 0)	
spi2_0.bpw = 8
spi2_0.mode = 1
# Init the SPI for the serial to parallel
spi2_1 = SPI(1, 1)	
spi2_1.bpw = 8
spi2_1.mode = 0

class SMD:

    all_smds = list()

    ''' Send the values to the serial to parallel chips '''
    @staticmethod
    def commit():        
        bytes = []
        for smd in SMD.all_smds:	   
            bytes.append(smd.getState())
        txt = ", ".join([hex(b) for b in bytes[::-1]])
        #logging.debug("Writing SPI: "+txt)
        spi2_1.writebytes(bytes[::-1])

    ''' Init'''
    def __init__(self, stepPin, dirPin, faultPin, dac_channel, name):
        self.dac_channel     = dac_channel  # Which channel on the dac is connected to this SMD
        self.stepPin         = stepPin
        self.dirPin          = dirPin
        self.faultPin        = faultPin
        self.name            = name
        self.state           = 0x70   	    # The state of the inputs
        self.dacvalue 	     = 0x00   	    # The voltage value on the VREF		
        self.enabled 	     = False	    # Start disabled
        self.currentPosition = 0.0 	        # Starts in pos 0
        self.set_position    = 0.0          # The desired position
        self.seconds_pr_step = 0.001        # Delay between each step (will be set by feed rate)
        self.steps_pr_mm     = 1            # Numer of steps pr mm. 
        self.debug           = 2            # Debug level
        self.direction       = 0            # Direction of movement
        self.moving          = False        # We start out stationary 
        self.microsteps      = 1.0          # Well, this is the microstep number
        self.pru_num         = -1           # PRU number, if any 
        SMD.all_smds.append(self) 	        # Add to list of smds
 						
    ''' Sets the SMD enabled '''
    def setEnabled(self, force_update=False):
        if not self.enabled:
            self.state &= ~(1<<6)
            self.enabled = True
        if force_update: 
            self.update()
            	
    ''' Sets the SMD disabled '''
    def setDisabled(self, force_update=False):
        if self.enabled:
            self.state |= (1<<6)
            self.enabled = False
        if force_update: 
            self.update()

    '''Logic high to enable device, logic low to enter
    low-power sleep mode. Internal pulldown.'''
    def enableSleepmode(self, force_update=False):
        self.state &= ~(1<<5)		
        if force_update: 
            self.update()


    ''' Disables sleepmode (awake) '''
    def disableSleepmode(self, force_update=False):
        self.state |= (1<<5)		
        if force_update: 
            self.update()

    '''nReset - Active-low reset input initializes the indexer
    logic and disables the H-bridge outputs.
    Internal pulldown.'''
    def reset(self, force_update=False):
        self.state &= ~(1<<4)
        self.update()
        time.sleep(0.001)
        self.state |= (1<<4)
        self.update()

    ''' Microstepping (default = 0) 0 to 5 '''
    def set_microstepping(self, value, force_update=False):
        self.microsteps = (1<<value) 
        self.state &= ~(7<<1)
        self.state |= (value << 1)
        self.mmPrStep = 1.0/(self.steps_pr_mm*self.microsteps)
        #logging.debug("State is: "+bin(self.state))
        #logging.debug("Microsteps: "+str(self.microsteps))
        #logging.debug("mmPrStep is: "+str(self.mmPrStep))
        if force_update: 
            self.update()

    def set_decay(self, value, force_update=False):
        ''' Decay mode, look in the data sheet '''
        self.state &= ~(1<<0)        # bit 0 
        self.state |= (value & 0x01) 
        if force_update: 
            self.update()

    ''' Current chopping limit (This is the value you can change) '''
    def setCurrentValue(self, iChop):        
        vRef = 3.3                              # Voltage reference on the DAC
        rSense = 0.1                            # Resistance for the 
        vOut = iChop*5.0*rSense                 # Calculated voltage out from the DAC 

        self.dacval = int((vOut*256.0)/vRef)
        byte1 = ((self.dacval & 0xF0)>>4) | (self.dac_channel<<4)
        byte2 = (self.dacval & 0x0F)<<4
        spi2_0.writebytes([byte1, byte2])       # Update all channels
        spi2_0.writebytes([0xA0, 0xFF])         # TODO: Change to only this channel (1<<dac_channel) ?


    ''' Returns the current state '''
    def getState(self):
        return self.state & 0xFF				# Return the state of the serial to parallel

    ''' Commits the changes	'''
    def update(self):
        SMD.commit()							# Commit the serial to parallel

    '''
    Higher level commands 
    '''

    ''' Set the feed rate in mm/min '''
    def setFeedRate(self, feed_rate):		
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
        return (1<<int(self.stepPin.split("_")[1]))
    
    ''' Get the dir pin shifted into position '''
    def get_dir_pin(self):
        return (1<<int(self.dirPin.split("_")[1]))




