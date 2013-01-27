''' xy_test.py - test script for testing fixed speed in PyPRUSS library'''

import pypruss as pru					# The Programmable Realtime Unit Library
import numpy as np						# Needed for braiding the pins with the delays

speed 			= 200 					# The travelling speed in mm/s
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
steps0 	  = [(1<<12), 0]*num_steps		# Make the table of ticks for the stepper. 
steps1 	  = [(1<<31), 0]*num_steps		# Make the table of ticks for the stepper. 
delays 	  = [inst_pr_step]*2*num_steps	# Make the table of delays

data0 = np.array([steps0, delays])		# Make a 2D matrix combining the ticks and delays
data0 = data0.transpose().flatten()		# Braid the data so every other item is a 
data0 = [num_steps*2+1]+list(data0)		# Make the data into a list and add the number of ticks total

data1 = np.array([steps1, delays])		# Make a 2D matrix combining the ticks and delays
data1 = data1.transpose().flatten()		# Braid the data so every other item is a 
data1 = [num_steps*2+1]+list(data1)		# Make the data into a list and add the number of ticks total

pru.init()								# Init
pru.exec_program(0, "./firmware.bin")	# load the firmware 
pru.exec_program(1, "./firmware.bin")	# Load the firmware
pru.disable(0)							# Clean shit up, we don't want to be piggies. 
pru.disable(1)							# Clean shit up, we don't want to be piggies. 
pru.write_memory(0, 0, data0)			# Load the data in the PRU ram
pru.write_memory(1, 0, data1)			# Load the data in the PRU ram
pru.enable(0)							# Clean shit up, we don't want to be piggies. 
pru.enable(1)							# Clean shit up, we don't want to be piggies. 
pru.wait_for_event(0)					# Wait a while for it to finish.
pru.wait_for_event(1)					# Wait a while for it to finish.


steps0 = list(np.array(steps0) + (1<<13))	# Make the table of ticks for the stepper. 
steps1 = list(np.array(steps1) + (1<<30))	# Make the table of ticks for the stepper. 

data0 = np.array([steps0, delays])		# Make a 2D matrix combining the ticks and delays
data0 = data0.transpose().flatten()		# Braid the data so every other item is a 
data0 = [num_steps*2+1]+list(data0)		# Make the data into a list and add the number of ticks total

data1 = np.array([steps1, delays])		# Make a 2D matrix combining the ticks and delays
data1 = data1.transpose().flatten()		# Braid the data so every other item is a 
data1 = [num_steps*2+1]+list(data1)		# Make the data into a list and add the number of ticks total

pru.disable(0)							# Clean shit up, we don't want to be piggies. 
pru.disable(1)							# Clean shit up, we don't want to be piggies. 
pru.write_memory(0, 0, data0)			# Load the data in the PRU ram
pru.write_memory(1, 0, data1)			# Load the data in the PRU ram
pru.enable(0)							# Clean shit up, we don't want to be piggies. 
pru.enable(1)							# Clean shit up, we don't want to be piggies. 
pru.wait_for_event(0)					# Wait a while for it to finish.
pru.wait_for_event(1)					# Wait a while for it to finish.


