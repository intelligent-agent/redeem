''' ddr_write.py - test script for writing to DDR memory using the PyPRUSS library'''

import pypruss
import mmap
import struct
import numpy as np

DDR_BASEADDR        = 0x70000000					# The actual baseaddr is 0x80000000, but due to a bug(?), 
DDR_HACK            = 0x10001000					# Python accept unsigned int as offset argument.
DDR_FILELEN         = DDR_HACK+0x1000				# The amount of memory to make available
DDR_OFFSET          = DDR_HACK						# Add the hack to the offset as well. 
DDR_MAGIC           = 0xbabe7175

#with open("/dev/mem", "r+b") as f:					# Open the memory device
#	ddr_mem = mmap.mmap(f.fileno(), DDR_FILELEN, offset=DDR_BASEADDR) # 

ddr_mem = mmap.mmap(0, 0x40000, offset=0x8c080000) # 


steps = [(3<<22), 0]*2								# 10 blinks, this control the GPIO1 pins
delays = [0xFFFFFF]*4								# number of delays. Each delay adds 2 instructions, so ~10ns

data = np.array([steps, delays])					# Make a 2D matrix combining the ticks and delays
data = data.transpose().flatten()					# Braid the data so every other item is a 
data = [4]+list(data)+[DDR_MAGIC]						# Make the data into a list and add the number of ticks total

str_data = ""										# Data in string form
for reg in data:									
	str_data += struct.pack('L', reg) 				# Make the data, it needs to be a string

print str_data.encode("hex")
ddr_mem[DDR_OFFSET:DDR_OFFSET+len(str_data)] = str_data	# Write the data to the DDR memory, four bytes should suffice
ddr_mem.close()										# Close the memory 
f.close()											# Close the file

pypruss.modprobe()							       	# This only has to be called once pr boot
pypruss.init()										# Init the PRU
pypruss.open(0)										# Open PRU event 0 which is PRU0_ARM_INTERRUPT
pypruss.pruintc_init()								# Init the interrupt controller
pypruss.exec_program(0, "./firmware_pru_0.bin")			# Load firmware "ddr_write.bin" on PRU 0
pypruss.wait_for_event(0)							# Wait for event 0 which is connected to PRU0_ARM_INTERRUPT
pypruss.clear_event(0)								# Clear the event
pypruss.pru_disable(0)								# Disable PRU 0, this is already done by the firmware
pypruss.exit()										# Exit, don't know what this does. 



