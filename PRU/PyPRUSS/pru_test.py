'''pru_test.py - test script for the PyPRUSS library'''

import pypruss as pru
import numpy as np
import time

pru_num = 0
pru.init(pru_num, "./firmware.bin")
delays = map(int, 1.0/(np.array(range(20))+1.0)*1000)
pins   = [(1<<12), 0]*10
data = [20]+list(np.array([pins, delays]).transpose().flatten())
pru.set_data(pru_num, data)
time.sleep(1)
pru.disable(pru_num)
