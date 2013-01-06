#!/usr/bin/python
''' 
Replicape main program
'''

from pwm import PWM

pwm = PWM()
pwm.setFrequency(100)
pwm.setDutyCycle(1, 0.7)
pwm.setDutyCycle(2, 0.5)
pwm.setDutyCycle(3, 0.1)
