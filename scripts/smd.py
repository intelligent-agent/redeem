#!/usr/bin/env python

from spi import SPI
import os
import time


# Make nFault X input
os.system("echo 0x2F > /sys/kernel/debug/omap_mux/gpmc_ad9")
# Make step and dir output
os.system("echo 0x07 > /sys/kernel/debug/omap_mux/gpmc_ad12")
os.system("echo 0x07 > /sys/kernel/debug/omap_mux/gpmc_ad13")
# Export the pins
os.system("echo 23 > /sys/class/gpio/export")
os.system("echo 44 > /sys/class/gpio/export")
os.system("echo 45 > /sys/class/gpio/export")

# Set direction
os.system("echo out > /sys/class/gpio/gpio44/direction")
os.system("echo out > /sys/class/gpio/gpio45/direction")

# Set the right value for the shift register

# Send the value
smd = SPI(2, 0)
smd.bpw = 8
smd.mode = 0

smd.writebytes([0b01110000]) # Enable
smd.writebytes([0b01110000]) # Enable
smd.writebytes([0b01110000]) # Enable
smd.writebytes([0b01110000]) # Enable
smd.writebytes([0b00110000]) # Enable with 1/32 step

# toggle the cs1-pin
os.system("echo 0x7 > /sys/kernel/debug/omap_mux/ecap0_in_pwm0_out")
os.system("echo 7 > /sys/class/gpio/export")
os.system("echo out >  /sys/class/gpio/gpio7/direction")
os.system("echo 1 > /sys/class/gpio/gpio7/value")
os.system("echo 0 > /sys/class/gpio/gpio7/value")
