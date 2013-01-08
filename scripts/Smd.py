#!/usr/bin/env python

'''
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
from bbio import *

# init the SPI
spi = SPI(2, 0)
spi.bpw = 8

# init the cs1-pin
pinMode(GPIO0_7, 0, 0)
digitalWrite(GPIO0_7, 0)

class SMD:

	all_smds = list()

	@staticmethod
	def commit():
		print "SMD commit"
		# First, update the serial to parallel reg
		spi.mode = 0
		for smd in SMD.all_smds:
			print "comitting to SMD: "+hex(smd.getState())
			spi.writebytes([smd.getState()])
		# toggle the cs1-pin
		digitalWrite(GPIO0_7, 0)
		digitalWrite(GPIO0_7, 1)

	def __init__(self, stepPin, dirPin, faultPin, dac_channel):
		self.dac_channel = dac_channel # Which channel on the dac is connected to this SMD
		self.stepPin  = stepPin
		self.dirPin   = dirPin
		self.faultPin = faultPin
		pinMode(stepPin,   0, 0) # Output, no pull up
		pinMode(dirPin,    0, 0) # Output, no pull up
		pinMode(faultPin,  1, 0) # Input, no pull up
		self.state 		= 0x70   # The state of the inputs
		self.dacvalue 	= 0x00   # The voltage value on the VREF
		
		self.setDelay(10)
		SMD.all_smds.append(self) # Add to list of smds
						
	# Sets the SMD enabled
	def setEnabled(self):
		print "Enabling SMD"
		self.state &= ~(1<<6)
		self.update()
		
	# Sets the SMD disabled
	def setDisabled(self):
		self.state |= (1<<6)
		self.update()
	
	'''Logic high to enable device, logic low to enter
	low-power sleep mode. Internal pulldown.'''
	# Enables sleepmode (low power)	
	def enableSleepmode(self):
		self.state &= ~(1<<5)		
		self.update()

	# Disables sleepmode (awake)
	def disableSleepmode(self):
		self.state |= (1<<5)		
		self.update()

	'''nReset - Active-low reset input initializes the indexer
	logic and disables the H-bridge outputs.
	Internal pulldown.'''
	def reset(self):
		self.state |= (1<<4)
		self.update()
		self.state &= ~(1<<4)
		self.update()

	# Microstepping (default = 0)
	def setMicrostepping(self, value):
		pass #TODO

	# Current chopping limit (This is the value you can change)
	def setCurrentValue(self, iChop):
		# Calculate the value for the DAC
		vRef = 3.3 # Voltage reference on the DAC
		rSense = 0.1 # Resistance for the 
		vOut = iChop*5.0*rSense # Calculated voltage out from the DAC (See page 9 in the datasheet for the DAC)
		self.dacval = int((vOut*256.0)/vRef)
		self.update()

	# Set the step-delay
	def setDelay(self, delay):
		self.stepDelay = delay

	# Toggle the "step" pin n times. 
	def step(self, steps):
		for i in range(steps):
			toggle(self.stepPin)
			delay(self.stepDelay)

	# Returns the current state
	def getState(self):
		return self.state

	# Commits the changes	
	def update(self):
		# Commit the serial to parallel
		SMD.commit()
		# Update the DAC
		spi.mode = 1
		byte1 = ((self.dacval & 0xF0)>>4) + (self.dac_channel<<4)
		byte2 = (self.dacval & 0x0F)<<4
		spi.writebytes([byte1, byte2])
		# Update all channels
		spi.writebytes([0xA0, 0xFF]) # TODO: Change to only this channel (1<<dac_channel) ?
			

