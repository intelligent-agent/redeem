''' accel_test.py - test script for testing fixed speed in PyPRUSS library'''

import pypruss as pru					# The Programmable Realtime Unit Library
import numpy as np						# Needed for braiding the pins with the delays
import time

max_speed 		= 80					# Top speed in mm/s
min_speed		= 0						# Minimum speed (V0). 
distance  		= 50					# The distance to travel in mm
acceleration 	= 200					# Acceleration in mm/s^2

microstepping 	= 2.0					# With microstepping, every step need four ticks.
steps_pr_mm		= 6.1*microstepping 	# Number of ticks the stepper needs to go one mm

pru_hz 			= 200*1000*1000			# The PRU has a speed of 200 MHz
s_pr_inst 		= 1.0/pru_hz			# I take it every instruction is a single cycle instruction
inst_pr_loop 	= 16					# This is the minimum number of instructions needed to step. 
inst_pr_delay 	= 2						# Every loop adds two instructions: i-- and i != 0

Vm	= max_speed/1000.0					# The travelling speed in m/s
a	= acceleration/1000.0				# Accelleration in m/s/s
s 	= distance/1000.0					# Distance in m
ds  = (1.0/(steps_pr_mm*1000.0))		# Delta S, distance in meters travelled pr step. 
u   = min_speed/1000.0					# Minimum speed in m/s

tm = (Vm-u)/a							# Calculate the time for when max speed is met. 
sm = u*tm+0.5*a*tm*tm					# Calculate the distace travelled when max speed is met

def t_by_s(s):							# Get the timestamp given a certain distance. 
	return (-u+np.sqrt(2*a*s+u*u))/a	# This is the s = ut+1/2at^2 solved with reference to t

def sec_to_inst(s):						# Shit, I'm missing MGP for this??
	inst_pr_step  = s/s_pr_inst  		# Calculate the number of instructions of delay pr step. 
	inst_pr_step /= 2.0					# To get a full period, we must divide by two. 
	inst_pr_step -= inst_pr_loop		# Remove the "must include" number of steps
	inst_pr_step /= inst_pr_delay		# Yes, this must be right..
	return int(inst_pr_step)			# Make it an int

distances = np.arange(0, sm, ds)		# Table of distances
t_in_s = map(t_by_s, distances)			# Make a table of times, the time at which a tick occurs
d_in_s = np.diff(t_in_s)/2.0			# We are more interested in the delays pr second. Half it, cos we will double it later
dd_in_s = np.array([d_in_s, d_in_s])	# Double the array 
dd_in_s = dd_in_s.transpose().flatten() # Transposing and flattening braids the data. 

num_steps = int(distance*steps_pr_mm)	# Number of ticks in total 
steps 	  = [(1<<12), 0]*num_steps		# Make the table of ticks for the stepper. 

delays 	  = map(sec_to_inst, dd_in_s)	# Number of instructions pr. step is now calculated
i_steps   = num_steps-len(delays)		# Find out how many delays are missing
i_dlys    = delays[-1::]*i_steps*2		# Make the intermediate steps
delays 	  = delays+i_dlys+delays[::-1]  # Add the missing delays. These are max_speed

data = np.array([steps, delays])		# Make a 2D matrix combining the ticks and delays
data = data.transpose().flatten()		# Braid the data so every other item is a 
data = [num_steps*2+1]+list(data)		# Make the data into a list and add the number of ticks total

s_pr_mm   		= 1.0/max_speed				# Seconds pr mm is the inverse of the mm/s
s_pr_step 		= s_pr_mm/steps_pr_mm	# To get the time to wait for each step, divide by mm/step

pru_num = 0								# PRU0 
pru.init(pru_num, "./firmware.bin")		# Load PRU 0 with the firmware. 
pru.set_data(pru_num, data)				# Load the data in the PRU ram
pru.wait_for_event(pru_num)				# Wait a while for it to finish.

''' Put your thing down, flip it and reverse it '''
steps = list(np.array(steps) + (1<<13))	# Make the table of ticks for the stepper. 

data = np.array([steps, delays])		# Make a 2D matrix combining the ticks and delays
data = data.transpose().flatten()		# Braid the data so every other item is a 
data = [num_steps*2+1]+list(data)		# Make the data into a list and add the number of ticks total

pru.set_data(pru_num, data)				# Load the data in the PRU ram
pru.wait_for_event(pru_num)				# Wait a while for it to finish.
time.sleep(1)
pru.disable(pru_num)					# Clean shit up, we don't want to be piggies. 

