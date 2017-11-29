# Measure voltage and current on input

import time
import spidev
spi = spidev.SpiDev()
spi.open(0, 1)


#Input voltage
def get_status():

    to_send = [0x00]*6*5
    res = spi.xfer(to_send)
    print(res)



# Turn on input
def enable_input():
    try:
        with open("/sys/class/gpio/export", "w") as f:
            f.write("18\n")
    except IOError: 
        pass
    with open("/sys/class/gpio/gpio18/direction", "w") as f:
        f.write("out\n")
    with open("/sys/class/gpio/gpio18/value", "w") as f:
        f.write("1\n")

enable_input()
get_status()
