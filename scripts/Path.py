''' accel_test.py - test script for testing fixed speed in PyPRUSS library'''

import numpy as np						        # Needed for braiding the pins with the delays

class Path: 	
    def __init__(self, x, y, z, e):
        self.x = x
        self.y = y
        self.z = z
        self.e = e

        hyp = np.sqrt(self.x**2+self.y**2)  # calculate the hypotenuse to the X-Y vectors, 
        self.length  = np.sqrt(hyp**2+self.z**2)     # Also include the z-travel          
            
    def calculate_delays(self, vec):
        ratio = vec/self.length                 # Calculate the ratio

        max_speed = 100					        # Top speed in mm/s
        min_speed = 0						    # Minimum speed (V0). 
        acceleration = 300					    # Acceleration in mm/s^2
        microstepping = 1.0					    # With microstepping, every step need four ticks.
        steps_pr_mm= 6.1*microstepping 	        # Number of ticks the stepper needs to go one mm

        Vm = max_speed*ratio/1000.0				# The travelling speed in m/s
        self.a  = acceleration*ratio/1000.0		# Accelleration in m/s/s
        s  = vec/1000.0					        # Distance in m
        ds = (1.0/(steps_pr_mm*1000.0))		    # Delta S, distance in meters travelled pr step. 
        self.u  = ratio*min_speed/1000.0		# Minimum speed in m/s

        tm = (Vm-self.u)/self.a					# Calculate the time for when max speed is met. 
        sm = self.u*tm+0.5*self.a*tm*tm			# Calculate the distace travelled when max speed is met
        
        if sm > s/2.0:
            sm = s/2.0            

        distances = np.arange(0, sm, ds)		# Table of distances
        t_in_s = map(self.t_by_s, distances)	# Make a table of times, the time at which a tick occurs
        d_in_s = np.diff(t_in_s)/2.0			# We are more interested in the delays pr second. Half it, cos we will double it later
        dd_in_s = np.array([d_in_s, d_in_s])	# Double the array so we have timings for up and down
        dd_in_s = dd_in_s.transpose().flatten() # Transposing and flattening braids the data. 
        
        return dd_in_s


    def t_by_s(self, s):							# Get the timestamp given a certain distance. 
        return (-self.u+np.sqrt(2*self.a*s+self.u*self.u))/self.a	# This is the s = ut+1/2at^2 solved with reference to t

