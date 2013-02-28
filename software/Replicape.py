#!/usr/bin/python
'''
Replicape main program. This should run on the BeagleBone.

Author: Elias Bakken
email: elias.bakken@gmail.com
Website: http://www.hipstercircuits.com
License: BSD

You can use and change this, but keep this heading :)
'''

import bbio as io
from math import sqrt
import time
import Queue 
import logging

from Mosfet import Mosfet
from Smd import SMD
from Thermistor import Thermistor
from Fan import Fan
from USB import USB
from Gcode import Gcode
import sys
from Extruder import Extruder, HBP
from Options import Options
from Pru import Pru
from Path import Path
from Path_planner import Path_planner
    
logging.basicConfig(level=logging.INFO)

class Replicape:
    ''' Init '''
    def __init__(self):
        # Init the IO library 
        io.bbio_init()

        # Make a list of steppers
        self.steppers = {}

        # Init the 5 Stepper motors
        self.steppers["X"]  = SMD(io.GPIO1_12, io.GPIO1_13, io.GPIO2_4,  5, "X")  # Fault_x should be PWM2A?
        self.steppers["Y"]  = SMD(io.GPIO1_31, io.GPIO1_30, io.GPIO1_15, 1, "Y")  
        self.steppers["Z"]  = SMD(io.GPIO1_1,  io.GPIO1_2,  io.GPIO0_27, 2, "Z")  
        self.steppers["E2"]  = SMD(io.GPIO3_21, io.GPIO1_7, io.GPIO2_1,  3, "Ext1")
        self.steppers["E"]  = SMD(io.GPIO1_14, io.GPIO1_6, io.GPIO2_3,  4, "Ext2")

        # Enable the steppers and set the current, steps pr mm and microstepping  
        self.steppers["X"].setCurrentValue(1.0) # 2A
        self.steppers["X"].setEnabled() 
        self.steppers["X"].set_steps_pr_mm(6.105)         
        self.steppers["X"].set_microstepping(2) 

        self.steppers["Y"].setCurrentValue(1.0) # 2A
        self.steppers["Y"].setEnabled() 
        self.steppers["Y"].set_steps_pr_mm(5.95)
        self.steppers["Y"].set_microstepping(2) 

        self.steppers["Z"].setCurrentValue(1.0) # 2A
        self.steppers["Z"].setEnabled() 
        self.steppers["Z"].set_steps_pr_mm(155)
        self.steppers["Z"].set_microstepping(2) 

        self.steppers["E"].setCurrentValue(1.0) # 2A        
        self.steppers["E"].setEnabled()
        self.steppers["E"].set_steps_pr_mm(5.0)
        self.steppers["E"].set_microstepping(2)

        # init the 3 thermistors
        self.therm_ext1 = Thermistor(io.AIN4, "Ext_1", chart_name="QU-BD")
        self.therm_hbp  = Thermistor(io.AIN6, "HBP", chart_name="B57560G104F")

        # init the 3 heaters
        self.mosfet_ext1 = Mosfet(io.PWM1A) # PWM2B on rev1
        self.mosfet_hbp  = Mosfet(io.PWM1B) # PWM1B on rev1 
        # Make extruder 1
        self.ext1 = Extruder(self.steppers["E"], self.therm_ext1, self.mosfet_ext1)
        self.ext1.setPvalue(0.5)
        self.ext1.setDvalue(0.1)     
        self.ext1.setIvalue(0.001)

        # Make Heated Build platform 
        self.hbp = HBP( self.therm_hbp, self.mosfet_hbp)       

        # Init the three fans
        self.fan_1 = Fan(1)
        self.fan_2 = Fan(2)
        self.fan_3 = Fan(3)

        # Make a queue of commands
        self.commands = Queue.Queue()

        # Set up USB, this receives messages and pushes them on the queue
        self.usb = USB(self.commands)		

        # Get all options 
        self.options = Options()

        # Init the path planner
        self.movement = "RELATIVE"
        self.feed_rate = 3000.0
        self.current_pos = {"X":0.0, "Y":0.0, "Z":0.0, "E":0.0}
        self.acceleration = 300.0/1000.0

        self.path_planner = Path_planner(self.steppers, self.current_pos)         
        self.path_planner.set_acceleration(self.acceleration) 
        logging.debug("Debug prints to console")
	
    ''' When a new gcode comes in, excute it '''
    def loop(self):
        try:
            while True:                
                gcode = Gcode(self.commands.get(), self)
                self._execute(gcode)
                self.usb.send_message(gcode.getAnswer())
                self.commands.task_done()
        except KeyboardInterrupt:
            print "Caught signal, exiting" 
            return
        finally:
            self.ext1.disable()
            self.hbp.disable()
            self.usb.close() 
            self.path_planner.exit()   
        logging.debug("Done")
		
    ''' Execute a G-code '''
    def _execute(self, g):
        if g.code() == "G1":                                        # Move (G1 X0.1 Y40.2 F3000)                        
            if g.hasLetter("F"):                                    # Get the feed rate                 
                feed_rate = float(g.getValueByLetter("F"))
                g.removeTokenByLetter("F")
            else:                                                   # If no feed rate is set in the command, use the default. 
                feed_rate = self.feed_rate                         
            smds = {}                                               # All steppers 
            for i in range(g.numTokens()):                          # Run through all tokens
                axis = g.tokenLetter(i)                             # Get the axis, X, Y, Z or E
                smds[axis] = float(g.tokenValue(i))                 # Get tha value, new position or vector             
            path = Path(smds, feed_rate, self.movement)             # Make a path segment from the axes            
            self.path_planner.add_path(path)                        # Add the path. This blocks until the path planner has capacity
        elif g.code() == "G21":                                     # Set units to mm
            self.factor = 1.0
        elif g.code() == "G28":                                     # Home the steppers
            if g.numTokens() == 0:                                  # If no token is given, home all
                g.setTokens(["X0", "Y0", "Z0"])                
            smds = {}                                               # All steppers 
            for i in range(g.numTokens()):                          # Run through all tokens
                axis = g.tokenLetter(i)                             # Get the axis, X, Y, Z or E
                smds[axis] = float(g.tokenValue(i))                 # Get tha value, new position or vector             
            path = Path(smds, self.feed_rate, "ABSOLUTE")           # Make a path segment from the axes
            self.path_planner.add_path(path)                        # Add the path. This blocks until the path planner has capacity
        elif g.code() == "G29": 
            print self.current_pos
        elif g.code() == "G90":                                     # Absolute positioning
            self.movement = "ABSOLUTE"
        elif g.code() == "G91":                                     # Relative positioning 
            self.movement = "RELATIVE"		
        elif g.code() == "G92":                                     # Set the current position of the following steppers
            if g.numTokens() == 0:
                 g.setTokens(["X0", "Y0", "Z0", "E0"])              # If no token is present, do this for all
            for i in range(g.numTokens()):
                axis = g.tokenLetter(i)
                val = float(g.tokenValue(i))
                self.path_planner.set_pos(axis, val)
        elif g.code() == "M17":                                     # Enable all steppers
            for name, stepper in self.steppers.iteritems():
                stepper.setEnabled()
        elif g.code() == "M30":                                     # Set microstepping (Propietary to Replicape)
            for i in range(g.numTokens()):
                self.steppers[g.tokenLetter(i)].set_microstepping(int(g.tokenValue(i)))            
        elif g.code() == "M84":                                     # Disable all steppers
            for name, stepper in self.steppers.iteritems():
            	stepper.setDisabled()
        elif g.code() == "M101":									# Deprecated 
            pass 													
        elif g.code() == "M103":									# Deprecated
            pass 													
        elif g.code() == "M104":                                    # Set extruder temperature
            self.ext1.setTargetTemperature(float(g.tokenValue(0)))
        elif g.code() == "M105":                                    # Get Temperature
            answer = "ok T:"+str(self.ext1.getTemperature())
            answer += " B:"+str(int(self.hbp.getTemperature()))
            g.setAnswer(answer)
        elif g.code() == "M106":                                    # Fan on
            self.fan_1.setPWMFrequency(100)
            self.fan_1.setValue(float(g.tokenValue(0)))	
        elif g.code() == "M108":									# Deprecated
            pass 													
        elif g.code() == "M110":                                    # Reset the line number counter 
            Gcode.line_number = 0       
        elif g.code() == "M130":                                    # Set PID P-value, Format (M130 P0 S8.0)
            pass
            #if int(self.tokens[0][1]) == 0:
            #    self.ext1.setPvalue(float(self.tokens[1][1::]))
        elif g.code() == "M131":                                    # Set PID I-value, Format (M131 P0 S8.0) 
            pass
            #if int(self.tokens[0][1]) == 0:
            #    self.p.ext1.setPvalue(float(self.tokens[1][1::]))
        elif g.code() == "M132":                                    # Set PID D-value, Format (M132 P0 S8.0)
            pass
            #if int(self.tokens[0][1]) == 0:
            #    self.p.ext1.setPvalue(float(self.tokens[1][1::]))
        elif g.code() == "M140":                                    # Set bed temperature
            self.hbp.setTargetTemperature(float(g.tokenValue(0)))
        else:
            print "Unknown command: "+g.message	
   
r = Replicape()
r.loop()

