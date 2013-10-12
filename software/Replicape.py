#!/usr/bin/python
'''
Replicape main program. This should run on the BeagleBone.

Author: Elias Bakken
email: elias.bakken@gmail.com
Website: http://www.hipstercircuits.com
License: BSD

You can use and change this, but keep this heading :)
'''

from math import sqrt
import time
import Queue 
import logging
import traceback
import os
import sys 
import ConfigParser

import profile

from Mosfet import Mosfet
from Smd import SMD
from Thermistor import Thermistor
from Fan import Fan
from EndStop import EndStop
from USB import USB
from Pipe import Pipe
from Ethernet import Ethernet
from Gcode import Gcode
import sys
from Extruder import Extruder, HBP
from Pru import Pru
from Path import Path
from Path_planner import Path_planner
from W1 import W1
    
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename='/var/log/replicape.log',
                    filemode='w')

def log_ex(type, value, traceback):
    logging.error('God damnit, not again!')
    logging.error('Type:'+str(type))
    logging.error('Value:'+str(value))
    logging.error('Traceback:'+str(traceback))

sys.excepthook = log_ex
version = "0.5.2"

print "Replicape v. "+version

class Replicape:
    ''' Init '''
    def __init__(self):
        logging.info("Replicape initializing "+version)
        self.config = ConfigParser.ConfigParser()
        self.config.readfp(open('config/default.cfg'))

        # Make a list of steppers
        self.steppers = {}

        # Init the 5 Stepper motors (step, dir, fault, DAC channel, name)
        self.steppers["X"] = SMD("GPIO0_27", "GPIO1_29", "GPIO2_4",  0, "X") 
        self.steppers["Y"] = SMD("GPIO1_12", "GPIO0_22", "GPIO2_5",  1, "Y")  
        self.steppers["Z"] = SMD("GPIO0_23", "GPIO0_26", "GPIO0_15", 2, "Z")  
        self.steppers["H"] = SMD("GPIO1_28", "GPIO1_15", "GPIO2_1",  3, "Ext1")
        self.steppers["E"] = SMD("GPIO1_13", "GPIO1_14", "GPIO2_3",  4, "Ext2")

        # Enable the steppers and set the current, steps pr mm and microstepping  
        for name, stepper in self.steppers.iteritems():
            stepper.setCurrentValue(self.config.getfloat('Steppers', 'current_'+name)) 
            stepper.setEnabled(self.config.getboolean('Steppers', 'enabled_'+name)) 
            stepper.set_steps_pr_mm(self.config.getfloat('Steppers', 'steps_pr_mm_'+name))         
            stepper.set_microstepping(self.config.getint('Steppers', 'microstepping_'+name)) 
            stepper.set_decay(0) 

		# Commit changes for the Steppers
        SMD.commit()

        # Find the path of the thermostors
        path = "/sys/bus/iio/devices/iio:device0/in_voltage"

        # init the 3 thermistors
        self.therm_ext1 = Thermistor(path+"4_raw", "MOSFET Ext 1", "B57560G104F")
        self.therm_hbp  = Thermistor(path+"6_raw", "MOSFET HBP",   "B57560G104F")
        self.therm_ext2 = Thermistor(path+"5_raw", "MOSFET Ext 2", "B57560G104F")

        if os.path.exists("/sys/bus/w1/devices/28-000002e34b73/w1_slave"):
            self.cold_end_1 = W1("/sys/bus/w1/devices/28-000002e34b73/w1_slave", "Cold End 1")
		
        # init the 3 heaters
        self.mosfet_ext1 = Mosfet(3)
        self.mosfet_ext2 = Mosfet(4)
        self.mosfet_hbp  = Mosfet(5)

        # Make extruder 1
        self.ext1 = Extruder(self.steppers["E"], self.therm_ext1, self.mosfet_ext1)
        self.ext1.setPvalue(0.010)
        self.ext1.setDvalue(0.3)     
        self.ext1.setIvalue(0.04)

        # Make Heated Build platform 
        self.hbp = HBP( self.therm_hbp, self.mosfet_hbp)       

        # Make extruder 2.
        self.ext2 = Extruder(self.steppers["H"], self.therm_ext2, self.mosfet_ext2)
        self.ext2.setPvalue(0.015)
        self.ext2.setDvalue(1.0)     
        self.ext2.setIvalue(0.03)

        # Init the three fans
        self.fan_1 = Fan(1)
        self.fan_2 = Fan(2)
        self.fan_3 = Fan(0)
        self.fans = {0: self.fan_1, 1:self.fan_2, 2:self.fan_3 }

        self.fan_1.setPWMFrequency(100)

        # Init the end stops
        self.end_stops = {}
        self.end_stops["Y1"] = EndStop("GPIO2_2", self.steppers, 1, "Y1")
        self.end_stops["X1"] = EndStop("GPIO0_14", self.steppers, 2, "X1")
        self.end_stops["Z1"] = EndStop("GPIO0_30", self.steppers, 3, "Z1")
        self.end_stops["Y2"] = EndStop("GPIO3_21", self.steppers, 4, "Y2")
        self.end_stops["X2"] = EndStop("GPIO0_31", self.steppers, 5, "X2")
        self.end_stops["Z2"] = EndStop("GPIO0_4", self.steppers, 6, "Z2")
        
        # Make a queue of commands
        self.commands = Queue.Queue(100)

        # Set up USB, this receives messages and pushes them on the queue
        #self.usb = USB(self.commands)		
        self.pipe = Pipe(self.commands)
        self.ethernet = Ethernet(self.commands)
        
        # Init the path planner
        self.movement = "RELATIVE"
        self.feed_rate = 3000.0
        self.current_pos = {"X":0.0, "Y":0.0, "Z":0.0, "E":0.0,"H":0.0}
        self.acceleration = 0.3
        self.axis_config = self.config.get('Geometry', 'axis_config')

        self.path_planner = Path_planner(self.steppers, self.current_pos)         
        self.path_planner.set_acceleration(self.acceleration) 
        self.stat = False

        # Signal everything ready
        logging.info("Replicape ready")
        print "Replicape ready" 
	
    ''' When a new gcode comes in, excute it '''
    def loop(self):
        print "Replicape starting main"
        try:
            while True:                
                global gcode
                gcode = Gcode(self.commands.get(), self)
                if self.stat:
                    global _o
                    _o = self
                    profile.run("_o._execute(gcode)")
                else:
                    self._execute(gcode)
                if gcode.prot == "USB":
                    self.usb.send_message(gcode.getAnswer())
                elif gcode.prot == "PIPE":
                    self.pipe.send_message(gcode.getAnswer())
                else:
                    self.ethernet.send_message(gcode.getAnswer())
                self.commands.task_done()
        except Exception as e:
            logging.exception("Ooops: ")
		
    ''' Execute a G-code '''
    def _execute(self, g):
        if g.code() == "G1":                                        # Move (G1 X0.1 Y40.2 F3000)                        
            if g.hasLetter("F"):                                    # Get the feed rate                 
                self.feed_rate = float(g.getValueByLetter("F"))/60000.0 # Convert from mm/min to SI unit m/s
                g.removeTokenByLetter("F")
            smds = {}                                               # All steppers 
            for i in range(g.numTokens()):                          # Run through all tokens
                axis = g.tokenLetter(i)                             # Get the axis, X, Y, Z or E
                smds[axis] = float(g.tokenValue(i))/1000.0          # Get the value, new position or vector             
            path = Path(smds, self.feed_rate, self.movement, g.is_crc(),  self.axis_config)# Make a path segment from the axes  
            self.path_planner.add_path(path)                        # Add the path. This blocks until the path planner has capacity
            #logging.debug("Moving to: "+' '.join('%s:%s' % i for i in smds.iteritems()))
        elif g.code() == "G21":                                     # Set units to mm
            self.factor = 1.0
        elif g.code() == "G28":                                     # Home the steppers
            if g.numTokens() == 0:                                  # If no token is given, home all
                g.setTokens(["X0", "Y0", "Z0"])                
            smds = {}                                               # All steppers 
            for i in range(g.numTokens()):                          # Run through all tokens
                axis = g.tokenLetter(i)                             # Get the axis, X, Y, Z or E
                smds[axis] = float(g.tokenValue(i))                 # Get tha value, new position or vector             
            path = Path(smds, self.feed_rate, "ABSOLUTE", False)           # Make a path segment from the axes
            #logging.debug("moving to "+str(smds))
            self.path_planner.add_path(path)                        # Add the path. This blocks until the path planner has capacity
        elif g.code() == "G90":                                     # Absolute positioning
            self.movement = "ABSOLUTE"
        elif g.code() == "G91":                                     # Relative positioning 
            self.movement = "RELATIVE"		
        elif g.code() == "G92":                                     # Set the current position of the following steppers
            self.path_planner.wait_until_done()
            if g.numTokens() == 0:
                logging.debug("G92: No tokens present")
                g.setTokens(["X0", "Y0", "Z0", "E0"])              # If no token is present, do this for all
            for i in range(g.numTokens()):
                axis = g.tokenLetter(i)
                val = float(g.tokenValue(i))
                self.path_planner.set_pos(axis, val)
        elif g.code() == "M17":                                     # Enable all steppers
            self.path_planner.wait_until_done()
            for name, stepper in self.steppers.iteritems():
                stepper.setEnabled() 
            SMD.commit()           
        elif g.code() == "M19":                                     # Reset all steppers
            self.path_planner.wait_until_done()
            for name, stepper in self.steppers.iteritems():
                stepper.reset() 
        elif g.code() == "M30":                                     # Set microstepping (Propietary to Replicape)
            for i in range(g.numTokens()):
                self.steppers[g.tokenLetter(i)].set_microstepping(int(g.tokenValue(i)))            
            SMD.commit() 
        elif g.code() == "M31":                                     # Set stepper current limit (Propietery to Replicape)
            for i in range(g.numTokens()):                         
                self.steppers[g.tokenLetter(i)].setCurrentValue(float(g.tokenValue(i)))            
            SMD.commit() 
        elif g.code() == "M84":                                     # Disable all steppers           
            self.path_planner.wait_until_done()
            for name, stepper in self.steppers.iteritems():
            	stepper.setDisabled()
            SMD.commit()           
        elif g.code() == "M92":                                     # M92: Set axis_steps_per_unit
            for i in range(g.numTokens()):                          # Run through all tokens
                axis = g.tokenLetter(i)                             # Get the axis, X, Y, Z or E
                self.steppers[axis].set_steps_pr_mm(float(g.tokenValue(i)))        
            SMD.commit() 
        elif g.code() == "M101":									# Deprecated 
            pass 													
        elif g.code() == "M103":									# Deprecated
            pass 													
        elif g.code() == "M104":                                    # Set extruder temperature
            self.ext1.setTargetTemperature(float(g.tokenValue(0)))
        elif g.code() == "M105":                                    # Get Temperature
            answer = "ok T:"+str(self.ext1.getTemperature())
            if hasattr(self, "hbp"):
                answer += " B:"+str(int(self.hbp.getTemperature()))
            if hasattr(self, "ext2"):
                answer += " T2:"+str(int(self.ext2.getTemperature()))
            if hasattr(self, "cold_end_1"):
                answer += " T3:"+str(int(self.cold_end_1.getTemperature()))         
            g.setAnswer(answer)
        elif g.code() == "M106":                                    # Fan on
            if g.hasLetter("P"):
                fan = self.fans[int(g.getValueByLetter("P"))]
                fan.setValue(float(g.getValueByLetter("S")))	                
            else:
                self.fan_1.setPWMFrequency(100)
                self.fan_1.setValue(float(g.tokenValue(0)))	
        elif g.code() == "M108":									# Deprecated
            pass 													
        elif g.code() == "M110":                                    # Reset the line number counter 
            Gcode.line_number = 0       
        elif g.code() == "M114": 
             g.setAnswer("ok C: "+' '.join('%s:%s' % i for i in self.current_pos.iteritems()))
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
        elif g.code() == "M141":
            fan = self.fans[int(g.getValueByLetter("P"))]
            fan.setPWMFrequency(int(g.getValueByLetter("F")))
            fan.setValue(float(g.getValueByLetter("S")))	           
        elif g.code() == "M142":
            self.stat = True 
        elif g.code() == "M143":
            self.stat = False 
        else:
            logging.warning("Unknown command: "+g.message)
   
r = Replicape()
r.loop()

