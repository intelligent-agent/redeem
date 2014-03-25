#!/usr/bin/python
'''
Redeem main program. This should run on the BeagleBone.

Author: Elias Bakken
email: elias(dot)bakken(at)gmail(dot)com
Website: http://www.thing-printer.com
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/

Minor verion tag is Arhold Schwartsnegger movies chronologically. 
'''

version = "0.11.1~Stay Hungry"

from math import sqrt
import time
import Queue 
import logging
import traceback
import os
import os.path
import sys 
import signal
import sys

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
from PruFirmware import PruFirmware
from CascadingConfigParser import CascadingConfigParser
from Printer import Printer
from GCodeProcessor import GCodeProcessor

logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M')

print "Redeem v. "+version

class Redeem:
    ''' Init '''
    def __init__(self):
        logging.info("Redeem initializing "+version)
        # Parse the config
        self.config = CascadingConfigParser(['/etc/redeem/default.cfg', '/etc/redeem/local.cfg'])

        # Get the revision from the Config file
        self.revision = self.config.get('System', 'revision', "A4")
        logging.info("Replicape revision "+self.revision)

        self.printer = Printer()

        # Init the end stops
        EndStop.callback = self.end_stop_hit
        EndStop.inputdev = self.config.get("Endstops","inputdev");

        if self.revision == "A4":
            self.printer.end_stops["X1"] = EndStop("GPIO3_21", 112, "X1", self.config.getboolean("Endstops", "invert_X1"))
            self.printer.end_stops["X2"] = EndStop("GPIO0_30", 113, "X2", self.config.getboolean("Endstops", "invert_X2"))
            self.printer.end_stops["Y1"] = EndStop("GPIO1_17", 114, "Y1", self.config.getboolean("Endstops", "invert_Y1"))
            self.printer.end_stops["Y2"] = EndStop("GPIO1_19", 115, "Y2", self.config.getboolean("Endstops", "invert_Y2"))
            self.printer.end_stops["Z1"] = EndStop("GPIO0_31", 116, "Z1", self.config.getboolean("Endstops", "invert_Z1"))
            self.printer.end_stops["Z2"] = EndStop("GPIO0_4" , 117, "Z2", self.config.getboolean("Endstops", "invert_Z2"))
        else:
            self.printer.end_stops["X1"] = EndStop("GPIO0_14", 112, "X1", self.config.getboolean("Endstops", "invert_X1"))
            self.printer.end_stops["X2"] = EndStop("GPIO3_21", 113, "X2", self.config.getboolean("Endstops", "invert_X2"))
            self.printer.end_stops["Y1"] = EndStop("GPIO2_2",  114, "Y1", self.config.getboolean("Endstops", "invert_Y1"))
            self.printer.end_stops["Y2"] = EndStop("GPIO0_31", 115, "Y2", self.config.getboolean("Endstops", "invert_Y2"))
            self.printer.end_stops["Z1"] = EndStop("GPIO0_30", 116, "Z1", self.config.getboolean("Endstops", "invert_Z1"))
            self.printer.end_stops["Z2"] = EndStop("GPIO0_4",  117, "Z2", self.config.getboolean("Endstops", "invert_Z2"))
            
        if self.revision == "A3":
            Stepper.revision = "A3"
            Stepper.ENABLED = 6
            Stepper.SLEEP   = 5
            Stepper.RESET   = 4
            Stepper.DECAY   = 0

        # Init the 5 Stepper motors (step, dir, fault, DAC channel, name)
        self.printer.steppers["X"] = Stepper("GPIO0_27", "GPIO1_29", "GPIO2_4",  0, "X",  self.printer.end_stops["X1"], 0,0) 
        self.printer.steppers["Y"] = Stepper("GPIO1_12", "GPIO0_22", "GPIO2_5",  1, "Y",  self.printer.end_stops["Y1"], 1,1)  
        self.printer.steppers["Z"] = Stepper("GPIO0_23", "GPIO0_26", "GPIO0_15", 2, "Z",  self.printer.end_stops["Z1"], 2,2)  
        self.printer.steppers["E"] = Stepper("GPIO1_28", "GPIO1_15", "GPIO2_1",  3, "Ext1", None,3,3)
        self.printer.steppers["H"] = Stepper("GPIO1_13", "GPIO1_14", "GPIO2_3",  4, "Ext2", None,4,4)

        # Enable the steppers and set the current, steps pr mm and microstepping  
        for name, stepper in self.printer.steppers.iteritems():
            stepper.set_current_value(self.config.getfloat('Steppers', 'current_'+name)) 
            if self.config.getboolean('Steppers', 'enabled_'+name):
                stepper.set_enabled()
            else:
                stepper.set_disabled()
            stepper.set_steps_pr_mm(self.config.getfloat('Steppers', 'steps_pr_mm_'+name))         
            stepper.set_microstepping(self.config.getint('Steppers', 'microstepping_'+name)) 
            stepper.direction = self.config.getint('Steppers', 'direction_'+name)
            stepper.set_decay(0)

		# Commit changes for the Steppers
        Stepper.commit()

        # Find the path of the thermistors
        path = "/sys/bus/iio/devices/iio:device0/in_voltage"

        # init the 3 thermistors
        therm_ext1 = Thermistor(path+"4_raw", "MOSFET Ext 1", self.config.get('Heaters', "ext1_temp_chart"))
        therm_hbp  = Thermistor(path+"6_raw", "MOSFET HBP",   self.config.get('Heaters', "hbp_temp_chart"))
        therm_ext2 = Thermistor(path+"5_raw", "MOSFET Ext 2", self.config.get('Heaters', "ext2_temp_chart"))

        path = self.config.get('Cold-ends', 'path', 0)
        if os.path.exists(path):
            self.printer.cold_ends[0] = ColdEnd(path, "Cold End 1")
            logging.info("Found Cold end on "+path)
        else:
            logging.info("No cold end present in path: "+path)            
		
        # Init the 3 heaters. Argument is channel number
        if self.revision == "A3":
          mosfet_ext1 = Mosfet(3)
          mosfet_ext2 = Mosfet(4)
          mosfet_hbp  = Mosfet(5)
        else:
          mosfet_ext1 = Mosfet(5)
          mosfet_ext2 = Mosfet(3)
          mosfet_hbp  = Mosfet(4)

        # Make extruder 1
        self.printer.heaters['E'] = Extruder(self.printer.steppers["E"], therm_ext1, mosfet_ext1, "Ext1", self.config.getboolean('Heaters', 'ext1_onoff_control'))
        self.printer.heaters['E'].set_p_value(self.config.getfloat('Heaters', "ext1_pid_p"))
        self.printer.heaters['E'].set_d_value(self.config.getfloat('Heaters', "ext1_pid_d"))
        self.printer.heaters['E'].set_i_value(self.config.getfloat('Heaters', "ext1_pid_i"))
        self.printer.heaters['E'].ok_range = self.config.getfloat('Heaters', "ext1_ok_range")

        # Make Heated Build platform 
        self.printer.heaters['HBP'] = HBP( therm_hbp, mosfet_hbp, self.config.getboolean('Heaters', 'hbp_onoff_control'))       
        self.printer.heaters['HBP'].set_p_value(self.config.getfloat('Heaters', "hbp_pid_p"))
        self.printer.heaters['HBP'].set_d_value(self.config.getfloat('Heaters', "hbp_pid_i"))     
        self.printer.heaters['HBP'].set_i_value(self.config.getfloat('Heaters', "hbp_pid_d"))
        self.printer.heaters['HBP'].ok_range = self.config.getfloat('Heaters', "hbp_ok_range")

        # Make extruder 2.
        self.printer.heaters['H'] = Extruder(self.printer.steppers["H"], therm_ext2, mosfet_ext2, "Ext2", self.config.getboolean('Heaters', 'ext2_onoff_control'))
        self.printer.heaters['H'].set_p_value(self.config.getfloat('Heaters', "ext2_pid_p"))
        self.printer.heaters['H'].set_d_value(self.config.getfloat('Heaters', "ext2_pid_i"))     
        self.printer.heaters['H'].set_i_value(self.config.getfloat('Heaters', "ext2_pid_d"))
        self.printer.heaters['H'].ok_range = self.config.getfloat('Heaters', "ext2_ok_range")        

        # Init the three fans. Argument is PWM channel number
        if self.revision == "A3":
            self.printer.fans[0] = Fan(0)
            self.printer.fans[1] = Fan(1)
            self.printer.fans[2] = Fan(2)
        else:
            self.printer.fans[0] = Fan(8)
            self.printer.fans[1] = Fan(9)
            self.printer.fans[2] = Fan(10)

        Fan.set_PWM_frequency(100)
         
        for i in self.printer:
            self.printer.fans[i].set_value(0)

        # Make a queue of commands
        self.commands = Queue.Queue(10)

        # Set up USB, this receives messages and pushes them on the queue
        self.usb = USB(self.commands)		
        # Virtual TTY 
        self.pipe = Pipe(self.commands)
        #self.pipe.set_send_reponse(False)
        self.ethernet = Ethernet(self.commands)
        
        # Init the path planner     
        Path.axis_config = int(self.config.get('Geometry', 'axis_config'))
        Path.max_speed_x = float(self.config.get('Steppers', 'max_speed_x'))
        Path.max_speed_y = float(self.config.get('Steppers', 'max_speed_y'))
        Path.max_speed_z = float(self.config.get('Steppers', 'max_speed_z'))
        Path.max_speed_e = float(self.config.get('Steppers', 'max_speed_e'))
        Path.max_speed_h = float(self.config.get('Steppers', 'max_speed_h'))

        Path.home_speed_x = float(self.config.get('Steppers', 'home_speed_x'))
        Path.home_speed_y = float(self.config.get('Steppers', 'home_speed_y'))
        Path.home_speed_z = float(self.config.get('Steppers', 'home_speed_z'))
        Path.home_speed_e = float(self.config.get('Steppers', 'home_speed_e'))
        Path.home_speed_h = float(self.config.get('Steppers', 'home_speed_h'))

        dirname = os.path.dirname(os.path.realpath(__file__))

        # Create the firmware compiler
        pru_firmware = PruFirmware(dirname+"/../firmware/firmware_runtime.p",dirname+"/../firmware/firmware_runtime.bin",dirname+"/../firmware/firmware_endstops.p",dirname+"/../firmware/firmware_endstops.bin",self.revision,self.config,"/usr/bin/pasm")

        self.printer.path_planner = PathPlanner(self.printer.steppers, pru_firmware)
        self.printer.path_planner.set_acceleration(float(self.config.get('Steppers', 'acceleration'))) 

        travel={}
        offset={}
        for axis in ['X','Y','Z']:
            travel[axis] = self.config.getfloat('Geometry', 'travel_'+axis.lower())
            offset[axis] = self.config.getfloat('Geometry', 'offset_'+axis.lower())

        self.printer.path_planner.set_travel_length(travel)
        self.printer.path_planner.set_center_offset(offset)

        self.processor = GCodeProcessor(self.printer);

        # After the firmwares are loaded, the endstop states can be updated.
        for k, endstop in self.printer.end_stops.iteritems():
            logging.debug("Endstop "+endstop.name+" hit? : "+ str(endstop.read_value()))

        self.running = True

        # Signal everything ready
        logging.info("Redeem ready")
	
    ''' When a new gcode comes in, excute it '''
    def loop(self):
        try:
            while self.running:
                try:
                    gcode = Gcode(self.commands.get(True,1.0))
                except Queue.Empty as e:
                    continue
                self._execute(gcode)
                self._reply(gcode)                
                self.commands.task_done()
        except Exception as e:
            logging.exception("Ooops: ")
		
    def exit(self):
        self.running = False
        self.printer.path_planner.force_exit()
        for name, stepper in self.printer.steppers.iteritems():
            stepper.set_disabled() 

        # Commit changes for the Steppers
        Stepper.commit()

    ''' Execute a G-code '''
    def _execute(self, g):  

        ret = self.processor.execute(g)

        #FIXME: Remote it once all commands moved to their per file counterpart.
        if ret != None:
            return

        if g.code() == "M19":                                         # Reset all steppers
            self.printer.path_planner.wait_until_done()
            for name, stepper in self.printer.steppers.iteritems():
                stepper.reset() 
        elif g.code() == "M30":                                         # Set microstepping (Propietary to Replicape)
            for i in range(g.num_tokens()):
                self.printer.steppers[g.token_letter(i)].set_microstepping(int(g.token_value(i)))            
            Stepper.commit() 
        elif g.code() == "M31":                                     # Set stepper current limit (Propietery to Replicape)
            for i in range(g.num_tokens()):                         
                self.printer.steppers[g.token_letter(i)].set_current_value(float(g.token_value(i)))            
            Stepper.commit() 
        elif g.code() == "M81": 
            os.system("shutdown now")
        elif g.code() == "M84" or g.code() == "M18":                # Disable all steppers           
            self.printer.path_planner.wait_until_done()
            if g.num_tokens() == 0:
                g.set_tokens(["X", "Y", "Z", "E", "H"])         # If no token is present, do this for all
                                             # All steppers 
            for i in range(g.num_tokens()):                          # Run through all tokens
                axis = g.token_letter(i)                             # Get the axis, X, Y, Z or E
                self.printer.steppers[axis].set_disabled()

            Stepper.commit()           
        elif g.code() == "M92":                                     # M92: Set axis_steps_per_unit
            for i in range(g.num_tokens()):                          # Run through all tokens
                axis = g.tokenLetter(i)                             # Get the axis, X, Y, Z or E
                self.printer.steppers[axis].set_steps_pr_mm(float(g.token_value(i)))        
            Stepper.commit() 
        elif g.code() == "M101":									# Deprecated 
            pass 													
        elif g.code() == "M103":									# Deprecated
            pass 													
        elif g.code() == "M104":                                    # Set extruder temperature
            if g.has_letter("P"): # Set hotend temp based on the P-param
                if int(g.get_value_by_letter("P")) == 0:
                    logging.debug("setting ext 0 temp to "+str(g.get_value_by_letter("S")))
                    self.printer.heaters['E'].set_target_temperature(float(g.get_value_by_letter("S")))
                elif int(g.get_value_by_letter("P")) == 1:
                    logging.debug("setting ext 1 temp to "+str(g.get_value_by_letter("S")))
                    self.printer.heaters['H'].set_target_temperature(float(g.get_value_by_letter("S")))
            else: # Change hotend temperature based on the chosen tool
                if self.printer.current_tool == "E":
                    logging.debug("setting ext 0 temp to "+str(g.token_value(0)))
                    self.printer.heaters['E'].set_target_temperature(float(g.token_value(0)))
                elif self.printer.current_tool == "H":
                    logging.debug("setting ext 1 temp to "+str(g.token_value(0)))
                    self.printer.heaters['H'].set_target_temperature(float(g.token_value(0)))                    
        elif g.code() == "M105":                                    # Get Temperature
            answer = "ok T:"+str(self.printer.heaters['E'].get_temperature())
            if hasattr(self, "hbp"):
                answer += " B:"+str(int(self.printer.heaters['HBP'].get_temperature()))
            if hasattr(self, "ext2"):
                answer += " T1:"+str(int(self.printer.heaters['H'].get_temperature()))
            if hasattr(self, "cold_end_1"):
                answer += " T2:"+str(int(self.cold_end_1.get_temperature()))         
            g.set_answer(answer)
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
        elif g.code() == "M112":                                    # Emergency stop
            #Reset PRU
            self.printer.path_planner.emergency_interrupt()          
        elif g.code() == "M114": 
            g.set_answer("ok C: "+' '.join('%s:%s' % i for i in self.printer.path_planner.current_pos.iteritems()))
        elif g.code() == "M116":  # Wait for all temperatures and other slowly-changing variables to arrive at their set values.
            all_ok = [False, False, False]
            while True:
                all_ok[0] |= self.printer.heaters['E'].is_target_temperature_reached()
                all_ok[1] |= self.printer.heaters['H'].is_target_temperature_reached()
                all_ok[2] |= self.printer.heaters['HBP'].is_target_temperature_reached()
                m105 = Gcode({"message": "M105", "prot": g.prot})
                self._execute(m105)
                print all_ok
                if not False in all_ok:
                    self._send_message(g.prot, "Heating done.")
                    self._reply(m105)
                    return 
                else:
                    answer = m105.get_answer()
                    answer += " E: "+ ("0" if self.printer.current_tool == "E" else "1")
                    m105.set_answer(answer[2:]) # strip away the "ok"
                    self._reply(m105)
                    time.sleep(1)
        elif g.code() == "M119": 
            g.set_answer("ok "+", ".join([v.name+": "+str(int(v.hit)) for k,v in self.printer.end_stops.iteritems()]))
        elif g.code() == "M130":                                    # Set PID P-value, Format (M130 P0 S8.0)
            pass
        elif g.code() == "M131":                                    # Set PID I-value, Format (M131 P0 S8.0) 
            pass
        elif g.code() == "M132":                                    # Set PID D-value, Format (M132 P0 S8.0)
            pass
        elif g.code() == "M140":                                    # Set bed temperature
            logging.debug("Setting bed temperature to "+str(float(g.token_value(0))))
            self.printer.heaters['HBP'].set_target_temperature(float(g.token_value(0)))
        elif g.code() == "M141":
            fan = self.printer.fans[int(g.get_value_by_letter("P"))]
            fan.set_PWM_frequency(int(g.get_value_by_letter("F")))
            fan.set_value(float(g.get_value_by_letter("S")))	           
        elif g.code() == "M190":
            self.printer.heaters['HBP'].set_target_temperature(float(g.get_value_by_letter("S")))
            self._execute(Gcode({"message": "M116", "prot": g.prot}))
        elif g.code() == "M400":
            self.printer.path_planner.wait_until_done()
        elif g.code() == "T0":                                      # Select tool 0
            self.printer.current_tool = "E"
        elif g.code() == "T1":                                      # select tool 1
            self.printer.current_tool = "H"
        elif g.message == "ok":
            pass
        else:
            logging.warning("Unknown command: "+g.message)
   

    ''' Send a reply through the proper channel '''
    def _reply(self, gcode):
        self._send_message(gcode.prot, gcode.get_answer())
    
    ''' Send a message back to host '''
    def _send_message(self, prot, msg):
        if prot == "USB":
            self.usb.send_message(msg)
        elif prot == "PIPE":
            self.pipe.send_message(msg)
        elif prot == "Eth":
            self.ethernet.send_message(msg)

    ''' An endStop has been hit '''
    def end_stop_hit(self, endstop):
        logging.warning("End Stop " + endstop.name +" hit!")

def signal_handler(signal, frame):
        print 'Cleaning up...'
        logging.info("KTHNXBYE!")
        r.exit()
        sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

r = Redeem()
r.loop()

