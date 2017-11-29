# Measure voltage and current on input

import time
from math import log

max_adc = 4095.0 # 12 bit


#Input voltage
def measure_voltage():
    signal = 0
    for i in range(100):
        with open("/sys/bus/iio/devices/iio:device0/in_voltage7_raw") as f:
            signal += float(f.read())*0.01
    R1 = 100000 # 100K
    R2 = 4700 #4.7K

    v_out = signal / max_adc * 1.8
    v_in = ((R1+R2)*v_out)/R2

    return v_in


# Input Current 

def measure_current():
    signal = 0
    for i in range(100):
        with open("/sys/bus/iio/devices/iio:device0/in_voltage6_raw") as f:
            signal += float(f.read())*0.01

    v_out = signal / max_adc * 1.8
    I = v_out *1000.0 / 50.0

    return I


# Board temperature
def measure_temp():
    signal = 0
    for i in range(100):
        with open("/sys/bus/iio/devices/iio:device0/in_voltage4_raw") as f:
            signal += float(f.read())*0.01

    R1 = 4700.0 # 4.7K
    R0 = 47000.0 # 47K
    B = 4131.0
    K = 273.15
    T0 = 25.0+K
    v_in = 1.8
    v_out = signal / max_adc * v_in
    R2 = (v_out*R1)/(v_in-v_out)    
    T1 = 1.0/T0 + (1.0/B)*log(R2/R0)
    
    return (1.0/T1)-K


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

def enable_heater(yes, chip=4):
    try:
        with open("/sys/class/pwm/pwmchip"+str(chip)+"/export", "w") as f:
            f.write("0\n")
    except IOError: 
        pass
    with open("/sys/class/pwm/pwm-"+str(chip)+":0/period", "w") as f:
        f.write("1000000\n")
    with open("/sys/class/pwm/pwm-"+str(chip)+":0/duty_cycle", "w") as f:
        f.write("500000\n")
    with open("/sys/class/pwm/pwm-"+str(chip)+":0/enable", "w") as f:
        f.write(str(yes)+"\n")


enable_heater(0, 4)
enable_heater(0, 5)
enable_heater(0, 6)
enable_heater(0, 7)
enable_input(0)

print("Input disabled")
v = measure_voltage()
i = measure_current()
t = measure_temp()
print("Voltage: {:.2f} current: {:.3f}, temp: {:.1f}".format(v, i, t))

enable_input(1)
enable_heater(1, 4)
enable_heater(1, 5)
enable_heater(1, 6)
enable_heater(1, 7)
print("Input and heater enabled")
for i in range(10):
    v = measure_voltage()
    i = measure_current()
    t = measure_temp()
    print("Voltage: {:.2f} current: {:.3f}, temp: {:.1f}".format(v, i, t))

enable_heater(0, 4)
enable_heater(0, 5)
enable_heater(0, 6)
enable_heater(0, 7)
enable_input(0)

print("Voltage: {:.2f} current: {:.3f}, temp: {:.1f}".format(v, i, t))

