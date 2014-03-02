#!/usr/bin/python
'''
Redeem main program. This should run on the BeagleBone.

Author: Elias Bakken
email: elias(dot)bakken(at)gmail(dot)com
Website: http://www.thing-printer.com
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/

Minor verion tag (starting from 0.8) is Arhold Schwartsnegger movies chronologically. 
'''

version = "0.9.0~The Long Goodbye"

from math import sqrt
import time
import Queue 
import logging
import traceback
import os
import os.path
import sys 
import ConfigParser

import profile

from Mosfet import Mosfet
from Stepper import Stepper
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
from PathPlanner import PathPlanner
from ColdEnd import ColdEnd
    
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M:%S',
                    filename='/var/log/redeem.log',
                    filemode='w')

def log_ex(type, value, traceback):
    logging.error('God damnit, not again!')
    logging.error('Type:'+str(type))
    logging.error('Value:'+str(value))
    logging.error('Traceback:'+str(traceback))

sys.excepthook = log_ex

print "Redeem v. "+version

class Redeem:
    ''' Init '''
    def __init__(self):
        logging.info("Redeem initializing "+version)
        self.config = ConfigParser.ConfigParser()
        config_filename = '/etc/redeem/default.cfg'
        if os.path.isfile(config_filename):
          self.config.readfp(open(config_filename))
        else:
          self.config.readfp(open("/usr/src/redeem/software/config/default.cfg"))  

        # Get the revision from the Config file
        self.revision = self.config.get('System', 'revision', "A4")
        logging.info("Replicape revision "+self.revision)

        # Make a list of steppers
        self.steppers = {}

        # Init the 5 Stepper motors (step, dir, fault, DAC channel, name)
        self.steppers["X"] = Stepper("GPIO0_27", "GPIO1_29", "GPIO2_4",  0, "X") 
        self.steppers["Y"] = Stepper("GPIO1_12", "GPIO0_22", "GPIO2_5",  1, "Y")  
        self.steppers["Z"] = Stepper("GPIO0_23", "GPIO0_26", "GPIO0_15", 2, "Z")  
        self.steppers["E"] = Stepper("GPIO1_28", "GPIO1_15", "GPIO2_1",  3, "Ext1")
        self.steppers["H"] = Stepper("GPIO1_13", "GPIO1_14", "GPIO2_3",  4, "Ext2")

        # Enable the steppers and set the current, steps pr mm and microstepping  
        for name, stepper in self.steppers.iteritems():
            stepper.set_current_value(self.config.getfloat('Steppers', 'current_'+name)) 
            stepper.set_enabled(self.config.getboolean('Steppers', 'enabled_'+name)) 
            stepper.set_steps_pr_mm(self.config.getfloat('Steppers', 'steps_pr_mm_'+name))         
            stepper.set_microstepping(self.config.getint('Steppers', 'microstepping_'+name)) 
            stepper.set_decay(0) 

    		# Commit changes for the Steppers
        Stepper.commit()

        # Find the path of the thermostors
        path = "/sys/bus/iio/devices/iio:device0/in_voltage"

        # init the 3 thermistors
        self.therm_ext1 = Thermistor(path+"4_raw", "MOSFET Ext 1", "B57561G0103F000") # Epcos 10K
        self.therm_hbp  = Thermistor(path+"6_raw", "MOSFET HBP",   "B57560G104F")	  # Epcos 100K
        self.therm_ext2 = Thermistor(path+"5_raw", "MOSFET Ext 2", "B57561G0103F000") # Epcos 10K

        path = self.config.get('Cold-ends', 'path', 0)
        if os.path.exists(path):
            self.cold_end_1 = ColdEnd(path, "Cold End 1")
            logging.info("Found Cold end on "+path)
        else:
            logging.info("No cold end present in path: "+path)            
		
        # Init the 3 heaters. Argument is channel number
        if self.revision == "A3":
          self.mosfet_ext1 = Mosfet(3)
          self.mosfet_ext2 = Mosfet(4)
          self.mosfet_hbp  = Mosfet(5)
        else:
          self.mosfet_ext1 = Mosfet(5)
          self.mosfet_ext2 = Mosfet(3)
          self.mosfet_hbp  = Mosfet(4)

        # Make extruder 1
        self.ext1 = Extruder(self.steppers["E"], self.therm_ext1, self.mosfet_ext1, "Ext1")
        self.ext1.set_p_value(self.config.getfloat('Heaters', "ext1_pid_p"))
        self.ext1.set_d_value(self.config.getfloat('Heaters', "ext1_pid_d"))
        self.ext1.set_i_value(self.config.getfloat('Heaters', "ext1_pid_i"))

        # Make Heated Build platform 
        self.hbp = HBP( self.therm_hbp, self.mosfet_hbp)       

        # Make extruder 2.
        self.ext2 = Extruder(self.steppers["H"], self.therm_ext2, self.mosfet_ext2, "Ext2")
        self.ext1.set_p_value(self.config.getfloat('Heaters', "ext2_pid_p"))
        self.ext1.set_d_value(self.config.getfloat('Heaters', "ext2_pid_i"))     
        self.ext1.set_i_value(self.config.getfloat('Heaters', "ext2_pid_d"))

        self.current_tool = "E" # Use Extruder 0 as default

        # Init the three fans. Argument is PWM channel number
        if self.revision == "A3":
            self.fan_1 = Fan(1)
            self.fan_2 = Fan(2)
            self.fan_3 = Fan(0)
        else:
            self.fan_1 = Fan(8)
            self.fan_2 = Fan(9)
            self.fan_3 = Fan(10)
        self.fans = {0: self.fan_1, 1:self.fan_2, 2:self.fan_3 }

        self.fan_1.setPWMFrequency(100)

        # Init the end stops
        self.end_stops = {}
        self.end_stops["X1"] = EndStop("GPIO3_21", self.steppers, 112, "X1")
        self.end_stops["X2"] = EndStop("GPIO0_30", self.steppers, 113, "X2")
        self.end_stops["Y1"] = EndStop("GPIO1_17", self.steppers, 114, "Y1")
        self.end_stops["Y2"] = EndStop("GPIO1_19", self.steppers, 115, "Y2")
        self.end_stops["Z1"] = EndStop("GPIO0_31", self.steppers, 116, "Z1")
        self.end_stops["Z2"] = EndStop("GPIO0_4",  self.steppers, 117, "Z2")
        
        # Make a queue of commands
        self.commands = Queue.Queue(10)

        # Set up USB, this receives messages and pushes them on the queue
        self.usb = USB(self.commands)		
        # Virtual TTY 
        self.pipe = Pipe(self.commands)
        #self.pipe.set_send_reponse(False)
        self.ethernet = Ethernet(self.commands)
        
        # Init the path planner
        self.movement = "RELATIVE"
        self.feed_rate = 3000.0
        self.current_pos = {"X":0.0, "Y":0.0, "Z":0.0, "E":0.0,"H":0.0}
        Path.axis_config = int(self.config.get('Geometry', 'axis_config'))
        Path.max_speed_x = float(self.config.get('Steppers', 'max_speed_x'))
        Path.max_speed_y = float(self.config.get('Steppers', 'max_speed_y'))
        Path.max_speed_z = float(self.config.get('Steppers', 'max_speed_z'))
        Path.max_speed_e = float(self.config.get('Steppers', 'max_speed_e'))
        Path.max_speed_h = float(self.config.get('Steppers', 'max_speed_h'))

        self.path_planner = PathPlanner(self.steppers, self.current_pos)         
        self.path_planner.set_acceleration(self.config.getfloat('Steppers', 'accelleration')) 

        

        # Signal everything ready
        logging.info("Redeem ready")
        print "Redeem ready" 
	
    ''' When a new gcode comes in, excute it '''
    def loop(self):
        try:
            while True:
                try:
                    gcode = Gcode(self.commands.get(True,1.0))
                except Queue.Empty as e:
                    continue
                self._execute(gcode)
                self._reply(gcode)                
                self.commands.task_done()
        except Exception as e:
            logging.exception("Ooops: ")
		
    ''' Execute a G-code '''
    def _execute(self, g):
        if g.code() == "G1" or g.code() == "G0":                                        # Move (G1 X0.1 Y40.2 F3000)                        
            if g.has_letter("F"):                                    # Get the feed rate                 
                self.feed_rate = float(g.get_value_by_letter("F"))/60000.0 # Convert from mm/min to SI unit m/s
                g.remove_token_by_letter("F")
            smds = {}                                               # All steppers 
            for i in range(g.num_tokens()):                          # Run through all tokens
                axis = g.token_letter(i)                             # Get the axis, X, Y, Z or E
                smds[axis] = float(g.token_value(i))/1000.0          # Get the value, new position or vector             
            if g.has_letter("E") and self.current_tool != "E":       # We are using a different tool, switch..
                smds[self.current_tool] = smds["E"]
                del smds["E"]
            path = Path(smds, self.feed_rate, self.movement, g.is_crc())# Make a path segment from the axes  
            self.path_planner.add_path(path)                        # Add the path. This blocks until the path planner has capacity
            #logging.debug("Moving to: "+' '.join('%s:%s' % i for i in smds.iteritems()))
        elif g.code() == "G21":                                     # Set units to mm
            self.factor = 1.0
        elif g.code() == "G28":                                     # Home the steppers
            if g.num_tokens() == 0:                                  # If no token is given, home all
                g.set_tokens(["X0", "Y0", "Z0"])                
            smds = {}                                               # All steppers 
            for i in range(g.num_tokens()):                          # Run through all tokens
                axis = g.token_letter(i)                             # Get the axis, X, Y, Z or E
                smds[axis] = float(g.token_value(i))                 # Get tha value, new position or vector             
            path = Path(smds, self.feed_rate, "ABSOLUTE", False)    # Make a path segment from the axes
            #logging.debug("moving to "+str(smds))
            self.path_planner.add_path(path)                        # Add the path. This blocks until the path planner has capacity
        elif g.code() == "G90":                                     # Absolute positioning
            self.movement = "ABSOLUTE"
        elif g.code() == "G91":                                     # Relative positioning 
            self.movement = "RELATIVE"		
        elif g.code() == "G92":                                     # Set the current position of the following steppers
            if g.num_tokens() == 0:
                logging.debug("Adding all to G92")
                g.set_tokens(["X0", "Y0", "Z0", "E0", "H0"])         # If no token is present, do this for all
            pos = {}                                               # All steppers 
            for i in range(g.num_tokens()):                          # Run through all tokens
                axis = g.token_letter(i)                             # Get the axis, X, Y, Z or E
                pos[axis] = float(g.token_value(i))/1000.0          # Get the value, new position or vector             
            if self.current_tool == "H": 
                logging.debug("Adding H to G92")
                pos["H"] = 0.0;
                del pos["E"]
            path = Path(pos, self.feed_rate, "G92")               # Make a path segment from the axes
            self.path_planner.add_path(path)  
        elif g.code() == "M17":                                     # Enable all steppers
            self.path_planner.wait_until_done()
            for name, stepper in self.steppers.iteritems():
                stepper.set_enabled() 
            Stepper.commit()           
        elif g.code() == "M19":                                     # Reset all steppers
            self.path_planner.wait_until_done()
            for name, stepper in self.steppers.iteritems():
                stepper.reset() 
        elif g.code() == "M30":                                     # Set microstepping (Propietary to Replicape)
            for i in range(g.num_tokens()):
                self.steppers[g.token_letter(i)].set_microstepping(int(g.token_value(i)))            
            Stepper.commit() 
        elif g.code() == "M31":                                     # Set stepper current limit (Propietery to Replicape)
            for i in range(g.num_tokens()):                         
                self.steppers[g.token_letter(i)].set_current_value(float(g.token_value(i)))            
            Stepper.commit() 
        elif g.code() == "M84" or g.code() == "M18":                # Disable all steppers           
            self.path_planner.wait_until_done()
            for name, stepper in self.steppers.iteritems():
            	stepper.set_disabled()
            Stepper.commit()           
        elif g.code() == "M92":                                     # M92: Set axis_steps_per_unit
            for i in range(g.num_tokens()):                          # Run through all tokens
                axis = g.tokenLetter(i)                             # Get the axis, X, Y, Z or E
                self.steppers[axis].set_steps_pr_mm(float(g.token_value(i)))        
            Stepper.commit() 
        elif g.code() == "M101":									# Deprecated 
            pass 													
        elif g.code() == "M103":									# Deprecated
            pass 													
        elif g.code() == "M104":                                    # Set extruder temperature
            if g.has_letter("P"): # Set hotend temp based on the P-param
                if int(g.get_value_by_letter("P")) == 0:
                    logging.debug("setting ext 0 temp to "+str(g.get_value_by_letter("S")))
                    self.ext1.set_target_temperature(float(g.get_value_by_letter("S")))
                elif int(g.get_value_by_letter("P")) == 1:
                    logging.debug("setting ext 1 temp to "+str(g.get_value_by_letter("S")))
                    self.ext2.set_target_temperature(float(g.get_value_by_letter("S")))
            else: # Change hotend temperature based on the chosen tool
                if self.current_tool == "E":
                    logging.debug("setting ext 0 temp to "+str(g.token_value(0)))
                    self.ext1.set_target_temperature(float(g.token_value(0)))
                elif self.current_tool == "H":
                    logging.debug("setting ext 1 temp to "+str(g.token_value(0)))
                    self.ext2.set_target_temperature(float(g.token_value(0)))                    
        elif g.code() == "M105":                                    # Get Temperature
            answer = "ok T:"+str(self.ext1.get_temperature())
            if hasattr(self, "hbp"):
                answer += " B:"+str(int(self.hbp.get_temperature()))
            if hasattr(self, "ext2"):
                answer += " T1:"+str(int(self.ext2.get_temperature()))
            if hasattr(self, "cold_end_1"):
                answer += " T2:"+str(int(self.cold_end_1.get_temperature()))         
            g.set_answer(answer)
        elif g.code() == "M106":                                    # Fan on
            if g.has_letter("P"):
                fan = self.fans[int(g.get_value_by_letter("P"))]
                fan.set_value(float(g.get_value_by_letter("S"))/255.0)     # According to reprap wiki, the number is 0..255
            elif g.num_tokens() == 1:
                self.fan_1.set_value(float(g.token_value(0))/255.0)
            else: # if there is no fan-number present, do it for the first fan
                self.fan_1.set_value(1.0)
                self.fan_2.set_value(1.0)
                self.fan_3.set_value(1.0)
        elif g.code() == "M108":									# Deprecated
            pass 													
        elif g.code() == "M109":
            logging.debug("M109 tokens is '"+" ".join(g.get_tokens())+"'")
            m104 = Gcode({"message": "M104 "+" ".join(g.get_tokens()), "prot": g.prot})
            self._execute(m104)
            m116 = Gcode({"message": "M116", "prot": g.prot})
            self._execute(m116)
        elif g.code() == "M110":                                    # Reset the line number counter 
            Gcode.line_number = 0       
        elif g.code() == "M114": 
            g.set_answer("ok C: "+' '.join('%s:%s' % i for i in self.current_pos.iteritems()))
        elif g.code() == "M116":  # Wait for all temperatures and other slowly-changing variables to arrive at their set values.
            while True:
                all_ok = True
                all_ok &= self.ext1.is_target_temperature_reached()
                all_ok &= self.ext2.is_target_temperature_reached()
                all_ok &= self.hbp.is_target_temperature_reached()
                m105 = Gcode({"message": "M105", "prot": g.prot})
                self._execute(m105)
                if all_ok:
                    self._reply(m105)
                    return 
                else:
                    answer = m105.get_answer()
                    m105.set_answer(answer[2:]) # strip away the "ok"
                    self._reply(m105)
                    time.sleep(1)
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
            logging.debug("Setting bed temperature to "+str(float(g.token_value(0))))
            self.hbp.set_target_temperature(float(g.token_value(0)))
        elif g.code() == "M141":
            fan = self.fans[int(g.get_value_by_letter("P"))]
            fan.setPWMFrequency(int(g.get_value_by_letter("F")))
            fan.set_value(float(g.get_value_by_letter("S")))	           
        elif g.code() == "M190":
            self.hbp.set_target_temperature(float(g.get_value_by_letter("S")))
        elif g.code() == "T0":                                      # Select tool 0
            self.current_tool = "E"
        elif g.code() == "T1":                                      # select tool 1
            self.current_tool = "H"
        else:
            logging.warning("Unknown command: "+g.message)
   

    ''' Send a reply through the proper channel '''
    def _reply(self, gcode):
        if gcode.prot == "USB":
            self.usb.send_message(gcode.get_answer())
        elif gcode.prot == "PIPE":
            self.pipe.send_message(gcode.get_answer())
        else:
            self.ethernet.send_message(gcode.get_answer())


r = Redeem()
r.loop()

