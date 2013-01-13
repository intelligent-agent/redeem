#!/usr/bin/python
''' 
Replicape main program
'''

import bbio as io

from Mosfet import Mosfet
from Smd import SMD
from Thermistor import Thermistor
from Fan import Fan
from USB import USB
from Gcode import Gcode
import sys
from Extruder import Extruder, HBP

class Replicape:
    def __init__(self):
        # init the 5 Stepper motors
        self.smd_x    = SMD(io.GPIO1_12, io.GPIO1_13, io.GPIO1_7, dac_channel=7)  # Fault_x should be PWM2A?
        self.smd_y    = SMD(io.GPIO1_12, io.GPIO1_13, io.GPIO1_7, dac_channel=1)  # Fault_x should be PWM2A?
        self.smd_z    = SMD(io.GPIO1_12, io.GPIO1_13, io.GPIO1_7, dac_channel=2)  # Fault_x should be PWM2A?
        self.smd_ext1 = SMD(io.GPIO1_12, io.GPIO1_13, io.GPIO1_7, dac_channel=3)  # Fault_x should be PWM2A?
        self.smd_ext2 = SMD(io.GPIO1_12, io.GPIO1_13, io.GPIO1_7, dac_channel=4)  # Fault_x should be PWM2A?

        # init the 3 thermistors
        self.therm_ext1 = Thermistor(io.AIN4)
        self.therm_ext2 = Thermistor(io.AIN5)
        self.therm_hbp  = Thermistor(io.AIN6)

        # init the 3 heaters
        self.mosfet_ext1 = Mosfet(io.PWM1A) # PWM2B on rev1
        #self.mosfet_ext2 = Mosfet(io.PWM2A) # PWM2A on rev1
        self.mosfet_hbp  = Mosfet(io.PWM1B) # PWM1B on rev1 

        # Make extruder 1
        self.ext1 = Extruder(self.smd_ext1, self.therm_ext1, self.mosfet_ext1)
        self.ext1.debugLevel(0)

        # Make Heated Build platform 
        self.hbp = HBP( self.therm_hbp, self.mosfet_hbp)
        self.hbp.debugLevel(1)

        # Init the three fans
        self.fan_1 = Fan(1)
        self.fan_2 = Fan(2)
        self.fan_3 = Fan(3)

        # Make a queue
        self.queue = list()
        # Set up USB, this receives message
        self.usb = USB(self.queue)		
	
    # When a new gcode comes in, excute it
    def loop(self):
        try:
            while True:
                if len(self.queue) > 0:
                    gcode = Gcode(self.queue.pop(0), self)
                    gcode.execute()
                    if gcode.hasAnswer():
                        self.usb.send_message(gcode.getAnswer())
                else:
                    io.delay(200)
        except KeyboardInterrupt:
            print "Caught signal, exiting" 
            return
        finally:
            self.cleanUp()  
		
    # Stop all threads
    def cleanUp(self):
        self.ext1.disable()
        self.hbp.disable()
        self.usb.close() 

    # Test some shit
    def test(self):
        self.smd_x.setCurrentValue(2.0) # 2A
        self.smd_x.setEnabled()
        self.smd_x.step(1000)
		
    # Test stepping	
    def step(self, delay):
        self.smd_x.setDelay(delay)
        self.smd_x.step(1000)
		

r = Replicape()
r.loop()

