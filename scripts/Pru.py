''' xy_test.py - test script for testing fixed speed in PyPRUSS library'''

import pypruss      					            # The Programmable Realtime Unit Library
import numpy as np						            # Needed for braiding the pins with the delays

class Pru:
    def __init__(self):
        pru_hz 			    = 200*1000*1000		    # The PRU has a speed of 200 MHz
        self.s_pr_inst 		= 1.0/pru_hz		    # I take it every instruction is a single cycle instruction
        self.inst_pr_loop 	= 16				    # This is the minimum number of instructions needed to step. 
        self.inst_pr_delay 	= 2					    # Every loop adds two instructions: i-- and i != 0

        pypruss.init()								# Init
        pypruss.write_memory(0, 0, [1, 0, 0, 0])
        pypruss.write_memory(1, 0, [1, 0, 0, 0])
        pypruss.exec_program(0, "./firmware.bin")	# load the firmware 
        pypruss.exec_program(1, "./firmware.bin")	# Load the firmware

    ''' Add some data to one of the PRUs '''
    def add_data(self, data, pru_num):
        (pins, delays) = data                       # Get the data
        print "pins   len:"+str(len(pins))
        print "delays len:"+str(len(delays))
        delays = map(self._sec_to_inst, delays)     # Convert the delays in secs to delays in instructions
        data = np.array([pins, delays])		        # Make a 2D matrix combining the ticks and delays
        data = data.transpose().flatten()		    # Braid the data so every other item is a pin and delay
        data = [len(pins)]+list(data)		        # Make the data into a list and add the number of ticks total        

        pypruss.disable(pru_num)					# Disable the PRU
        pypruss.write_memory(pru_num, 0, data)		# Load the data in the PRU ram

    ''' Enable the pru '''
    def go(self):
        pypruss.enable(0)							    # Start the thing
        pypruss.enable(1)							    # Start the other thing

    ''' Wait for the PRU to finish '''                
    def wait_for_event(self):
        pypruss.wait_for_event(0)					    # Wait a while for it to finish.
        pypruss.wait_for_event(1)					    # Wait a while for it to finish.

    ''' Convert delay in seconds to number of instructions for the PRU '''
    def _sec_to_inst(self, s):					    # Shit, I'm missing MGP for this??
        inst_pr_step  = s/self.s_pr_inst  		    # Calculate the number of instructions of delay pr step. 
        inst_pr_step /= 2.0					        # To get a full period, we must divide by two. 
        inst_pr_step -= self.inst_pr_loop		    # Remove the "must include" number of steps
        inst_pr_step /= self.inst_pr_delay		    # Yes, this must be right..
        return int(inst_pr_step)			        # Make it an int
