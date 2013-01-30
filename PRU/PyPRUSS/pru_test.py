'''pru_test.py - test script for the PyPRUSS library'''

import pypruss as pru
import numpy as np
import time

print "starting "
pru.init_all()
print "Waiting"
pru.wait_for_both()
print "done!"
pru.disable(0)					                # Disable the PRU
pru.disable(1)					                # Disable the PRU
data = [101]+[(1<<13), 0xFF, 0, 0xFF]*50
pru.write_memory(0, 0, data)	# Load the data in the PRU ram
pru.write_memory(1, 0, data)	# Load the data in the PRU ram
pru.enable(0)						            # Start the thing
pru.enable(1)						            # Start the thing
pru.wait_for_both()

'''pru_num = 0
pru.init(pru_num, "./firmware.bin")
delays = map(int, 1.0/(np.array(range(20))+1.0)*1000)
pins   = [(1<<12), 0]*10
data = [20]+list(np.array([pins, delays]).transpose().flatten())
pru.set_data(pru_num, data)
time.sleep(1)
pru.disable(pru_num)
'''
