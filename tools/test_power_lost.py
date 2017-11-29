# Measure voltage and current on input

import time
from math import log

max_adc = 4095.0 # 12 bit


#Input voltage
def measure_voltage():
    signal = 0
    for i in range(1):
        with open("/sys/bus/iio/devices/iio:device0/in_voltage7_raw") as f:
            signal += float(f.read())
    R1 = 100000 # 100K
    R2 = 4700 #4.7K

    v_out = signal / max_adc * 1.8
    v_in = ((R1+R2)*v_out)/R2

    return v_in

# Turn on input
def enable_input(yes):
    try:
        with open("/sys/class/gpio/export", "w") as f:
            f.write("18\n")
    except IOError: 
        pass
    with open("/sys/class/gpio/gpio18/direction", "w") as f:
        f.write("out\n")
    with open("/sys/class/gpio/gpio18/value", "w") as f:
        f.write(str(yes)+"\n")


def enable_heater(yes):
    try:
        with open("/sys/class/pwm/pwmchip6/export", "w") as f:
            f.write("0\n")
    except IOError: 
        pass
    with open("/sys/class/pwm/pwm-6:0/period", "w") as f:
        f.write("1000000\n")
    with open("/sys/class/pwm/pwm-6:0/duty_cycle", "w") as f:
        f.write("500000\n")
    with open("/sys/class/pwm/pwm-6:0/enable", "w") as f:
        f.write(str(yes)+"\n")

print("Enabling input. Pull power to see what happens")
enable_input(1)
enable_heater(1)
while 1:
    v = measure_voltage()
    if v < 5.0:        
        print("power lost!")
        enable_input(0)
        secs = 0
        while 1:
            time.sleep(1)
            secs += 1
            print("Power lasted "+str(secs)+" seconds")
