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

from Mosfet import Mosfet
from Smd import SMD
from Thermistor import Thermistor
from Fan import Fan
from USB import USB
#from Pipe import Pipe
from Ethernet import Ethernet
from Gcode import Gcode
import sys
from Extruder import Extruder, HBP
from Pru import Pru
from Path import Path
from Path_planner import Path_planner
    
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename='/var/log/replicape.log',
                    filemode='w')

class Replicape:
    ''' Init '''
    def __init__(self):
        logging.info("Replicape initializing")

        # Make a list of steppers
        self.steppers = {}

        logging.info("Init steppers")
        # Init the 5 Stepper motors (step, dir, fault, DAC channel, name)
        self.steppers["X"] = SMD("GPIO0_27", "GPIO1_29", "GPIO2_4",  0, "X") 
        self.steppers["Y"] = SMD("GPIO1_12", "GPIO0_22", "GPIO2_5",  1, "Y")  
        self.steppers["Z"] = SMD("GPIO0_23", "GPIO0_26", "GPIO0_15", 2, "Z")  
        self.steppers["H"] = SMD("GPIO1_28", "GPIO1_15", "GPIO2_1",  3, "Ext1")
        self.steppers["E"] = SMD("GPIO1_13", "GPIO1_14", "GPIO2_2",  4, "Ext2")

        # Enable the steppers and set the current, steps pr mm and microstepping  
        logging.info("Enabling steppers")
        self.steppers["X"].setCurrentValue(1.0) 
        self.steppers["X"].setEnabled() 
        self.steppers["X"].set_steps_pr_mm(4.3)         
        self.steppers["X"].set_microstepping(2) 

        self.steppers["Y"].setCurrentValue(1.0) 
        self.steppers["Y"].setEnabled() 
        self.steppers["Y"].set_steps_pr_mm(4.3)
        self.steppers["Y"].set_microstepping(2) 

        self.steppers["Z"].setCurrentValue(1.5) 
        self.steppers["Z"].setEnabled() 
        self.steppers["Z"].set_steps_pr_mm(50)
        self.steppers["Z"].set_microstepping(2) 

        self.steppers["E"].setCurrentValue(1.5) 
        self.steppers["E"].setEnabled()
        self.steppers["E"].set_steps_pr_mm(5.0)
        self.steppers["E"].set_microstepping(2)

        # Find the path of the thermostors
        path = ""
        for dev in os.listdir("/sys/devices/ocp.2/"):
            if dev.startswith("thermistors"):
                path = "/sys/devices/ocp.2/"+dev+"/"
                break

        logging.debug("Found thermistors at "+path)

        # init the 3 thermistors
        logging.info("Init Thermistors")
        self.therm_ext1 = Thermistor(path+"AIN4", "MOSFET Ext 1", "B57560G104F")
        self.therm_hbp  = Thermistor(path+"AIN6", "MOSFET HBP",   "B57560G104F")
        self.therm_ext2 = Thermistor(path+"AIN5", "MOSFET Ext 2", "B57560G104F")

        # init the 3 heaters
        self.mosfet_ext1 = Mosfet(3)
        self.mosfet_ext2 = Mosfet(4)
        self.mosfet_hbp  = Mosfet(5)

        # Make extruder 1
        self.ext1 = Extruder(self.steppers["E"], self.therm_ext1, self.mosfet_ext1)
        self.ext1.setPvalue(0.02)
        self.ext1.setDvalue(0.9)     
        self.ext1.setIvalue(0.01)

        # Make Heated Build platform 
        self.hbp = HBP( self.therm_hbp, self.mosfet_hbp)       

        # Init the three fans
        self.fan_1 = Fan(1)
        self.fan_2 = Fan(2)
        self.fan_3 = Fan(0)
        self.fans = {0: self.fan_1, 1:self.fan_2, 2:self.fan_3 }

        self.fan_1.setPWMFrequency(100)


        # Make a queue of commands
        self.commands = Queue.Queue(30)

        # Set up USB, this receives messages and pushes them on the queue
        self.usb = USB(self.commands)		
        #self.pipe = Pipe(self.commands)
        self.ethernet = Ethernet(self.commands)
        
        # Init the path planner
        self.movement = "RELATIVE"
        self.feed_rate = 3000.0
        self.current_pos = {"X":0.0, "Y":0.0, "Z":0.0, "E":0.0}
        self.acceleration = 100.0/1000.0

        self.path_planner = Path_planner(self.steppers, self.current_pos)         
        self.path_planner.set_acceleration(self.acceleration) 
        logging.info("Replicape ready")
	
    ''' When a new gcode comes in, excute it '''
    def loop(self):
        try:
            while True:                
                gcode = Gcode(self.commands.get(), self)
                self._execute(gcode)
                if gcode.prot == "USB":
                    self.usb.send_message(gcode.getAnswer())
                elif gcode.prot == "PIPE":
                    self.pipe.send_message(gcode.getAnswer())
                else:
                    self.ethernet.send_message(gcode.getAnswer())
                self.commands.task_done()
        except KeyboardInterrupt:
            logging.info("Caught keyboard interrupt signal, exiting")
            return
        except Exception as e:
            logging.error("Something whent wrong..")
            logging.error(traceback.format_exc())
        finally:			
            self.ext1.disable()            
            self.hbp.disable()            
            self.usb.close() 
            self.pipe.close()
            self.path_planner.exit()   
		
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
            logging.debug("moving to "+str(smds))
            self.path_planner.add_path(path)                        # Add the path. This blocks until the path planner has capacity
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
        elif g.code() == "M31":                                     # Set stepper current limit (Propietery to Replicape)
            for i in range(g.numTokens()):                         
                self.steppers[g.tokenLetter(i)].setCurrentValue(float(g.tokenValue(i)))            
        elif g.code() == "M84":                                     # Disable all steppers           
            self.path_planner.wait_until_done()
            for name, stepper in self.steppers.iteritems():
            	stepper.setDisabled()
        elif g.code() == "M92": 
            for i in range(g.numTokens()):                          # Run through all tokens
                axis = g.tokenLetter(i)                             # Get the axis, X, Y, Z or E
                self.steppers[axis].set_steps_pr_mm(float(g.tokenValue(i)))        
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
        else:
            logging.warning("Unknown command: "+g.message)
   
r = Replicape()
r.loop()

