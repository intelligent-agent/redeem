#!/usr/bin/env python

import os
import time


for i in range(100):
	os.system("echo 0 > /sys/class/gpio/gpio44/value")
	os.system("echo 1 > /sys/class/gpio/gpio44/value")
		
