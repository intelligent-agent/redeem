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
from Options import Options

class Replicape:
    ''' Init '''
    def __init__(self):
        # Init the IO library 
        io.bbio_init()

        # Make a list of steppers
        self.steppers = {}

        # Init the 5 Stepper motors
        self.steppers["X"]  = SMD(io.GPIO1_12, io.GPIO1_13, io.GPIO1_7, 7, "X")  # Fault_x should be PWM2A?
        self.steppers["Y"]  = SMD(io.GPIO1_31, io.GPIO1_30, io.GPIO1_15, 1, "Y")  # Fault_x should be PWM2A?
        self.steppers["Z"]  = SMD(io.GPIO1_1, io.GPIO2_2, io.GPIO0_27, 2, "Z")  # Fault_x should be PWM2A?
        self.steppers["E"]  = SMD(io.GPIO3_21, io.GPIO3_19, io.GPIO2_3, 4, "Ext1")  # Fault_x should be PWM2A?
        self.steppers["E2"] = SMD(io.GPIO1_12, io.GPIO1_13, io.GPIO1_7, 3, "Ext2")  # Fault_x should be PWM2A?


        # Enable the steppers and set current 
        self.steppers["X"].setCurrentValue(3.0) # 2A
        self.steppers["X"].setEnabled() 
        self.steppers["Y"].setCurrentValue(3.0) # 2A
        self.steppers["Y"].setEnabled() 
        self.steppers["Z"].setCurrentValue(3.0) # 2A
        self.steppers["Z"].setEnabled() 
        self.steppers["E"].setCurrentValue(2.0) # 2A        
        self.steppers["E"].setEnabled()
        self.steppers["E2"].setCurrentValue(0.0) # 2A        
        self.steppers["E2"].setEnabled()

        # 
        #for stepper in self.steppers:
        #    stepper.setCurrentValue(2.0) # 2A
        #    stepper.setEnabled()

        # init the 3 thermistors
        self.therm_ext1 = Thermistor(io.AIN4, "Ext_1", chart_name="QU-BD")
        #self.therm_ext2 = Thermistor(io.AIN5, "Ext_2")
        self.therm_hbp  = Thermistor(io.AIN6, "HBP", chart_name="B57560G104F")
        #self.therm_hbp.setDebugLevel(2)

        # init the 3 heaters
        self.mosfet_ext1 = Mosfet(io.PWM1A) # PWM2B on rev1
        #self.mosfet_ext2 = Mosfet(io.PWM2A) # PWM2A on rev1
        self.mosfet_hbp  = Mosfet(io.PWM1B) # PWM1B on rev1 

        # Make extruder 1
        self.ext1 = Extruder(self.steppers["E"], self.therm_ext1, self.mosfet_ext1)
        #self.ext1.debugLevel(1)

        # Make Heated Build platform 
        self.hbp = HBP( self.therm_hbp, self.mosfet_hbp)
        #self.hbp.debugLevel(1)

        # Init the three fans
        self.fan_1 = Fan(1)
        self.fan_2 = Fan(2)
        self.fan_3 = Fan(3)

        # Make a queue of commands
        self.queue = list()

        # Set up USB, this receives messages and pushes them on the queue
        self.usb = USB(self.queue)		

        # Get all options 
        self.options = Options()

        # Make the positioning vector
        self.position = {"x": 0, "y": 0, "z": 0}
	
    ''' When a new gcode comes in, excute it '''
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
		
    ''' Stop all threads '''
    def cleanUp(self):
        self.ext1.disable()
        self.hbp.disable()
        self.usb.close() 

    ''' Switch to absolute positioning '''
    def setPositionAbsolute(self):
        self.position = "ABSOLUTE"

    ''' Switch to relative positioning '''
    def setPositionRelative(self):
        self.position = "RELATIVE"

    ''' Move the stepper motors '''
    def move(self, stepper, amount, feed_rate):
        print "Moving "+stepper+" "+str(amount)+" mm"
        self.steppers[stepper].move(amount)
    
    ''' Disable all steppers '''
    def disableAllSteppers(self):
        for name, stepper in self.steppers.iteritems():
            stepper.setDisabled()

		

r = Replicape()
r.loop()

