'''pru_test.py - test script for the PyPRUSS library'''

import pypruss as pru

pru_num = 0

pru.init(pru_num)
delays = [1, 16]*3
pins   = [(1<<12), 0]*3
print pins
print delays
pru.set_data(pru_num, pins, delays)
pru.disable(pru_num)
