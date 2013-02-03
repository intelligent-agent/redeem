#!/usr/bin/python 

# Import PyBBIO library:
from bbio import *
import numpy as np

therm1 = AIN6 # pin 37 on header P9

# This conversion table has been found in the datasheet for B57560G104F
temp_chart = [
[0, 333964],
[5, 258497], 
[10, 201659], 
[15, 158499], 
[20, 125468], 
[25, 100000], 
[30, 80223], 
[35, 64759], 
[40, 52589], 
[45, 42951], 
[50, 35272],
[55, 29119], 
[60, 24161], 
[65, 20144], 
[70, 16874], 
[75, 14198], 
[80, 11998], 
[85, 10181], 
[90, 8674], 
[95, 7419], 
[100, 6369], 
[105, 5487], 
[110, 4744], 
[115, 4115], 
[120, 3581], 
[125, 3126], 
[130, 2737],
[135, 2404], 
[140, 2117], 
[145, 1869], 
[150, 1655], 
[155, 1469], 
[160, 1307], 
[165, 1166], 
[170, 1043], 
[175, 934.5], 
[180, 839.3], 
[185, 755.4], 
[190, 681.3], 
[195, 615.8], 
[200, 557.6], 
[205, 505.9], 
[210, 459.9], 
[215, 418.8], 
[220, 382.0], 
[225, 349.1], 
[230, 319.5], 
[235, 292.9], 
[240, 269.0], 
[245, 247.3], 
[250, 227.8], 
[255, 210.1], 
[260, 194.1], 
[265, 179.5], 
[270, 166.3], 
[275, 154.2], 
[280, 143.2], 
[285, 133.2], 
[290, 124.0], 
[295, 115.5], 
[300, 107.8]]

# Transpose the chart
temp_chart = map(list, zip(*temp_chart))

# Return the temperature nearest to the resistor value
def resistance_to_degrees(resistor_val):
    idx = (np.abs(np.array(temp_chart[1])-resistor_val)).argmin()
    return temp_chart[0][idx]

# Convert the voltage to a resistance value
def voltage_to_resistance(v_sense):
    return  4700.0/((1.8/v_sense)-1.0)

# Read thermistor value and print the result
def readThermistor():
    # Get the ADC values
    adc_val = 0
    for i in range(1000):
        adc_val+= analogRead(therm1)
    adc_val /= 1000.0
    voltage = inVolts(adc_val)                 # Convert to voltage
    res_val = voltage_to_resistance(voltage)    # Convert to resistance    
    temperature = resistance_to_degrees(res_val) # Convert to degrees
    print " AIN6 ADC value: %i - voltage: %fv - thermistor res: %f - Temperature: %f deg." % (adc_val, voltage, res_val, temperature)
    #delay(500)

# Start the loop:
while 1:
    readThermistor()

