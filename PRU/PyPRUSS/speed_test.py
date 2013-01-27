''' speed_test.py - test script for testing fixed speed in PyPRUSS library'''

import pypruss as pru					# The Programmable Realtime Unit Library
import numpy as np						# Needed for braiding the pins with the delays

speed 			= 80 					# The travelling speed in mm/s
distance 		= 50					# Distance in mm

microstepping 	= 2.0					# With microstepping, every step need four ticks.
steps_pr_mm		= 6.1*microstepping 	# Number of ticks the stepper needs to go one mm

pru_hz 			= 200*1000*1000			# The PRU has a speed of 200 MHz
s_pr_inst 		= 1.0/pru_hz			# I take it every instruction is a single cycle instruction
inst_pr_loop 	= 16					# This is the minimum number of instructions needed to step. 
inst_pr_delay 	= 2						# Every loop adds two instructions: i-- and i != 0

s_pr_mm   		= 1.0/speed				# Seconds pr mm is the inverse of the mm/s
s_pr_step 		= s_pr_mm/steps_pr_mm	# To get the time to wait for each step, divide by mm/step

inst_pr_step  = s_pr_step/s_pr_inst  	# Calculate the number of instructions of delay pr step. 
inst_pr_step /= 2.0						# To get a full period, we must divide by two. 
inst_pr_step -= inst_pr_loop			# Remove the "must include" number of steps
inst_pr_step /= inst_pr_delay			# Yes, this must be right..
inst_pr_step  = int(inst_pr_step)		# Make it an int

num_steps = int(distance*steps_pr_mm)	# Number of ticks in total 
steps 	  = [(1<<12), 0]*num_steps		# Make the table of ticks for the stepper. 
delays 	  = [inst_pr_step]*2*num_steps	# Make the table of delays

data = np.array([steps, delays])		# Make a 2D matrix combining the ticks and delays
data = data.transpose().flatten()		# Braid the data so every other item is a 
data = [num_steps*2+1]+list(data)		# Make the data into a list and add the number of ticks total

pru_num = 0								# PRU0 
pru.init(pru_num, "./firmware.bin")		# Load PRU 0 with the firmware. 
pru.set_data(pru_num, data)				# Load the data in the PRU ram
pru.wait_for_event(pru_num)				# Wait a while for it to finish.
pru.disable(pru_num)					# Clean shit up, we don't want to be piggies. 

''' Put your thing down, flip it and reverse it '''
steps = list(np.array(steps) + (1<<13))	# Make the table of ticks for the stepper. 

data = np.array([steps, delays])		# Make a 2D matrix combining the ticks and delays
data = data.transpose().flatten()		# Braid the data so every other item is a 
data = [num_steps*2+1]+list(data)		# Make the data into a list and add the number of ticks total

pru_num = 0								# PRU0 
pru.init(pru_num, "./firmware.bin")		# Load PRU 0 with the firmware. 
pru.set_data(pru_num, data)				# Load the data in the PRU ram
pru.wait_for_event(pru_num)				# Wait a while for it to finish.
pru.disable(pru_num)					# Clean shit up, we don't want to be piggies. 

