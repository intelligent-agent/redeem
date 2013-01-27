''' xy_test.py - test script for testing fixed speed in PyPRUSS library'''

import pypruss as pru					# The Programmable Realtime Unit Library
import numpy as np						# Needed for braiding the pins with the delays

from Path import Path


x = 50
y = 50

pru_hz 			= 200*1000*1000			# The PRU has a speed of 200 MHz
s_pr_inst 		= 1.0/pru_hz			# I take it every instruction is a single cycle instruction
inst_pr_loop 	= 16					# This is the minimum number of instructions needed to step. 
inst_pr_delay 	= 2						# Every loop adds two instructions: i-- and i != 0

microstepping = 1.0					    # With microstepping, every step need four ticks.
steps_pr_mm= 6.1*microstepping 	        # Number of ticks the stepper needs to go one mm

def sec_to_inst(s):						# Shit, I'm missing MGP for this??
	inst_pr_step  = s/s_pr_inst  		# Calculate the number of instructions of delay pr step. 
	inst_pr_step /= 2.0					# To get a full period, we must divide by two. 
	inst_pr_step -= inst_pr_loop		# Remove the "must include" number of steps
	inst_pr_step /= inst_pr_delay		# Yes, this must be right..
	return int(inst_pr_step)			# Make it an int


path = Path(x,y,0,0)
delays_x = path.calculate_delays(x)
delays_y = path.calculate_delays(y)
delays_x  = map(sec_to_inst, delays_x)	# Number of instructions pr. step is now calculated
delays_y  = map(sec_to_inst, delays_y)	# Number of instructions pr. step is now calculated

num_steps_x = int(x*steps_pr_mm)		# Number of ticks in total 
num_steps_y = int(y*steps_pr_mm)		# Number of ticks in total 
steps_x     = [(1<<12), 0]*num_steps_x	# Make the table of ticks for the stepper. 
steps_y 	= [(1<<31), 0]*num_steps_y


i_steps_x  = num_steps_x-len(delays_x)		# Find out how many delays are missing
i_steps_y  = num_steps_y-len(delays_y)		# Find out how many delays are missing
i_dlys_x   = delays_x[-1::]*i_steps_x*2		# Make the intermediate steps
i_dlys_y   = delays_y[-1::]*i_steps_y*2		# Make the intermediate steps
delays_x   = delays_x+i_dlys_x+delays_x[::-1]  # Add the missing delays. These are max_speed
delays_y   = delays_y+i_dlys_y+delays_y[::-1]  # Add the missing delays. These are max_speed

print "delays_x len: "+str(len(delays_x))
print "delays_y len: "+str(len(delays_y))
print "steps_x len: "+str(len(steps_x))
print "steps_y len: "+str(len(steps_y))

pru.init()								# Init
pru.exec_program(0, "./firmware.bin")	# load the firmware 
pru.exec_program(1, "./firmware.bin")	# Load the firmware

while True:	
    steps_x     = [(1<<12)+(1<<13), (1<<13)]*num_steps_x	# Make the table of ticks for the stepper. 
    steps_y 	= [(1<<31)+(1<<30), (1<<30)]*num_steps_y

    data_x = np.array([steps_x, delays_x])		# Make a 2D matrix combining the ticks and delays
    data_x = data_x.transpose().flatten()		# Braid the data so every other item is a 
    data_x = [num_steps_x*2+1]+list(data_x)		# Make the data into a list and add the number of ticks total

    data_y = np.array([steps_y, delays_y])		# Make a 2D matrix combining the ticks and delays
    data_y = data_y.transpose().flatten()		# Braid the data so every other item is a 
    data_y = [num_steps_y*2+1]+list(data_y)		# Make the data into a list and add the number of ticks total

    print "forward"
    pru.disable(0)							    # Clean shit up, we don't want to be piggies. 
    pru.disable(1)							    # Clean shit up, we don't want to be piggies. 
    pru.write_memory(0, 0, data_x)			    # Load the data in the PRU ram
    pru.write_memory(1, 0, data_y)			    # Load the data in the PRU ram
    pru.enable(0)							    # Clean shit up, we don't want to be piggies. 
    pru.enable(1)							    # Clean shit up, we don't want to be piggies. 
    pru.wait_for_event(0)					    # Wait a while for it to finish.
    #pru.wait_for_event(1)					    # Wait a while for it to finish.

    steps_x     = [(1<<12), 0]*num_steps_x	    # Make the table of ticks for the stepper. 
    steps_y 	= [(1<<31), 0]*num_steps_y

    data_x = np.array([steps_x, delays_x])		# Make a 2D matrix combining the ticks and delays
    data_x = data_x.transpose().flatten()		# Braid the data so every other item is a 
    data_x = [num_steps_x*2+1]+list(data_x)		# Make the data into a list and add the number of ticks total

    data_y = np.array([steps_y, delays_y])		# Make a 2D matrix combining the ticks and delays
    data_y = data_y.transpose().flatten()		# Braid the data so every other item is a 
    data_y = [num_steps_y*2+1]+list(data_y)		# Make the data into a list and add the number of ticks total

    print "Back again"
    pru.disable(0)							    # Clean shit up, we don't want to be piggies. 
    pru.disable(1)							    # Clean shit up, we don't want to be piggies. 
    pru.write_memory(0, 0, data_x)			    # Load the data in the PRU ram
    pru.write_memory(1, 0, data_y)			    # Load the data in the PRU ram
    pru.enable(0)							    # Clean shit up, we don't want to be piggies. 
    pru.enable(1)							    # Clean shit up, we don't want to be piggies. 
    pru.wait_for_event(0)					    # Wait a while for it to finish.
    #pru.wait_for_event(1)					    # Wait a while for it to finish.

