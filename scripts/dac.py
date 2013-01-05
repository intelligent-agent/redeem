#!/usr/bin/env python

from spi import SPI

# Set up the SPI
dac = SPI(2, 0)
dac.mode = 1 # SPI mode 1
dac.bpw = 8  # 8 bits pr word
dac.lsbfirst = False # MSB transfers

# Calculate the value for the DAC
iChop = 2.0 # Current chopping limit (This is the value you can change)
vRef = 3.3 # Voltage reference on the DAC
rSense = 0.1 # Resistance for the 
vOut = iChop*5.0*rSense # Calculated voltage out from the DAC (See page 9 in the datasheet for the DAC)
dacval = int((vOut*256.0)/vRef)

# Update all channels with the value
for addr in range(8):
	byte1 = ((dacval & 0xF0)>>4) + (addr<<4)
	byte2 = (dacval & 0x0F)<<4
	dac.writebytes([byte1, byte2])
# Update all channels
dac.writebytes([0xA0, 0xFF])

print "All channels now have vOut = "+str(vOut)+", iChop = "+str(iChop)
