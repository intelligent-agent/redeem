#!/usr/bin/python
'''
Redeem main program. This should run on the BeagleBone.

Author: Elias Bakken
email: elias(dot)bakken(at)gmail(dot)com
Website: http://www.thing-printer.com
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/

Minor verion tag is Arhold Schwartsnegger movies chronologically. 
'''

version = "0.12.0~The Villain"

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
from Path import Path, RelativePath, AbsolutePath, G92Path
from PathPlanner import PathPlanner
from ColdEnd import ColdEnd
from PruFirmware import PruFirmware
from CascadingConfigParser import CascadingConfigParser
from Printer import Printer
from GCodeProcessor import GCodeProcessor

logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M')

class Redeem:
    ''' Init '''
    def __init__(self):
        logging.info("Redeem initializing "+version)

        self.printer = Printer()

        # Parse the config
        self.printer.config = CascadingConfigParser(['/etc/redeem/default.cfg', '/etc/redeem/local.cfg'])

        # Get the revision from the Config file
        self.revision = self.printer.config.get('System', 'revision', "A4")
        logging.info("Replicape revision "+self.revision)

        

        # Init the end stops
        EndStop.callback = self.end_stop_hit
        EndStop.inputdev = self.printer.config.get("Endstops","inputdev");

        if self.revision == "A4" or self.revision == "A4A":
            self.printer.end_stops["X1"] = EndStop("GPIO3_21", 112, "X1", self.printer.config.getboolean("Endstops", "invert_X1"))
            self.printer.end_stops["X2"] = EndStop("GPIO0_30", 113, "X2", self.printer.config.getboolean("Endstops", "invert_X2"))
            self.printer.end_stops["Y1"] = EndStop("GPIO1_17", 114, "Y1", self.printer.config.getboolean("Endstops", "invert_Y1"))
            self.printer.end_stops["Y2"] = EndStop("GPIO1_19", 115, "Y2", self.printer.config.getboolean("Endstops", "invert_Y2"))
            self.printer.end_stops["Z1"] = EndStop("GPIO0_31", 116, "Z1", self.printer.config.getboolean("Endstops", "invert_Z1"))
            self.printer.end_stops["Z2"] = EndStop("GPIO0_4" , 117, "Z2", self.printer.config.getboolean("Endstops", "invert_Z2"))
        else:
            self.printer.end_stops["X1"] = EndStop("GPIO0_14", 112, "X1", self.printer.config.getboolean("Endstops", "invert_X1"))
            self.printer.end_stops["X2"] = EndStop("GPIO3_21", 113, "X2", self.printer.config.getboolean("Endstops", "invert_X2"))
            self.printer.end_stops["Y1"] = EndStop("GPIO2_2",  114, "Y1", self.printer.config.getboolean("Endstops", "invert_Y1"))
            self.printer.end_stops["Y2"] = EndStop("GPIO0_31", 115, "Y2", self.printer.config.getboolean("Endstops", "invert_Y2"))
            self.printer.end_stops["Z1"] = EndStop("GPIO0_30", 116, "Z1", self.printer.config.getboolean("Endstops", "invert_Z1"))
            self.printer.end_stops["Z2"] = EndStop("GPIO0_4",  117, "Z2", self.printer.config.getboolean("Endstops", "invert_Z2"))
            
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
            stepper.set_current_value(self.printer.config.getfloat('Steppers', 'current_'+name)) 
            if self.printer.config.getboolean('Steppers', 'enabled_'+name):
                stepper.set_enabled()
            else:
                stepper.set_disabled()
            stepper.set_steps_pr_mm(self.printer.config.getfloat('Steppers', 'steps_pr_mm_'+name))         
            stepper.set_microstepping(self.printer.config.getint('Steppers', 'microstepping_'+name)) 
            stepper.direction = self.printer.config.getint('Steppers', 'direction_'+name)
            stepper.set_decay(self.printer.config.getboolean("Steppers", "slow_decay_"+name))

		# Commit changes for the Steppers
        Stepper.commit()

        # Find the path of the thermistors
        path = "/sys/bus/iio/devices/iio:device0/in_voltage"

        # init the 3 thermistors
        therm_ext1 = Thermistor(path+"4_raw", "MOSFET Ext 1", self.printer.config.get('Heaters', "ext1_temp_chart"))
        therm_hbp  = Thermistor(path+"6_raw", "MOSFET HBP",   self.printer.config.get('Heaters', "hbp_temp_chart"))
        therm_ext2 = Thermistor(path+"5_raw", "MOSFET Ext 2", self.printer.config.get('Heaters', "ext2_temp_chart"))

        path = self.printer.config.get('Cold-ends', 'path', 0)
        if os.path.exists(path):
            self.printer.cold_ends.append(ColdEnd(path, "Cold End 1"))
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
        self.printer.heaters['E'] = Extruder(self.printer.steppers["E"], therm_ext1, mosfet_ext1, "Ext1", self.printer.config.getboolean('Heaters', 'ext1_onoff_control'))
        self.printer.heaters['E'].set_p_value(self.printer.config.getfloat('Heaters', "ext1_pid_p"))
        self.printer.heaters['E'].set_d_value(self.printer.config.getfloat('Heaters', "ext1_pid_d"))
        self.printer.heaters['E'].set_i_value(self.printer.config.getfloat('Heaters', "ext1_pid_i"))
        self.printer.heaters['E'].ok_range = self.printer.config.getfloat('Heaters', "ext1_ok_range")

        # Make Heated Build platform 
        self.printer.heaters['HBP'] = HBP( therm_hbp, mosfet_hbp, self.printer.config.getboolean('Heaters', 'hbp_onoff_control'))       
        self.printer.heaters['HBP'].set_p_value(self.printer.config.getfloat('Heaters', "hbp_pid_p"))
        self.printer.heaters['HBP'].set_d_value(self.printer.config.getfloat('Heaters', "hbp_pid_i"))     
        self.printer.heaters['HBP'].set_i_value(self.printer.config.getfloat('Heaters', "hbp_pid_d"))
        self.printer.heaters['HBP'].ok_range = self.printer.config.getfloat('Heaters', "hbp_ok_range")

        # Make extruder 2.
        self.printer.heaters['H'] = Extruder(self.printer.steppers["H"], therm_ext2, mosfet_ext2, "Ext2", self.printer.config.getboolean('Heaters', 'ext2_onoff_control'))
        self.printer.heaters['H'].set_p_value(self.printer.config.getfloat('Heaters', "ext2_pid_p"))
        self.printer.heaters['H'].set_d_value(self.printer.config.getfloat('Heaters', "ext2_pid_i"))     
        self.printer.heaters['H'].set_i_value(self.printer.config.getfloat('Heaters', "ext2_pid_d"))
        self.printer.heaters['H'].ok_range = self.printer.config.getfloat('Heaters', "ext2_ok_range")        

        # Init the three fans. Argument is PWM channel number
        self.printer.fans=[]
        if self.revision == "A3":
            self.printer.fans.append(Fan(1))
            self.printer.fans.append(Fan(2))
            self.printer.fans.append(Fan(0))
        else:
            self.printer.fans.append(Fan(8))
            self.printer.fans.append(Fan(9))
            self.printer.fans.append(Fan(10))

        Fan.set_PWM_frequency(100)
         
        for f in self.printer.fans:
            f.set_value(0)

        # Make a queue of commands
        self.commands = Queue.Queue(10)
        
        # Init the path planner
        Path.axis_config = int(self.printer.config.get('Geometry', 'axis_config'))
        Path.max_speeds[0] = float(self.printer.config.get('Steppers', 'max_speed_x'))
        Path.max_speeds[1] = float(self.printer.config.get('Steppers', 'max_speed_y'))
        Path.max_speeds[2] = float(self.printer.config.get('Steppers', 'max_speed_z'))
        Path.max_speeds[3] = float(self.printer.config.get('Steppers', 'max_speed_e'))
        Path.max_speeds[4] = float(self.printer.config.get('Steppers', 'max_speed_h'))

        Path.home_speed[0] = float(self.printer.config.get('Steppers', 'home_speed_x'))
        Path.home_speed[1] = float(self.printer.config.get('Steppers', 'home_speed_y'))
        Path.home_speed[2] = float(self.printer.config.get('Steppers', 'home_speed_z'))
        Path.home_speed[3] = float(self.printer.config.get('Steppers', 'home_speed_e'))
        Path.home_speed[4] = float(self.printer.config.get('Steppers', 'home_speed_h'))

        Path.steps_pr_meter[0] = self.printer.steppers["X"].get_steps_pr_meter()
        Path.steps_pr_meter[1] = self.printer.steppers["Y"].get_steps_pr_meter()
        Path.steps_pr_meter[2] = self.printer.steppers["Z"].get_steps_pr_meter()
        Path.steps_pr_meter[3] = self.printer.steppers["E"].get_steps_pr_meter()
        Path.steps_pr_meter[4] = self.printer.steppers["H"].get_steps_pr_meter()
 

        dirname = os.path.dirname(os.path.realpath(__file__))

        # Create the firmware compiler
        pru_firmware = PruFirmware(dirname+"/../firmware/firmware_runtime.p",dirname+"/../firmware/firmware_runtime.bin",dirname+"/../firmware/firmware_endstops.p",dirname+"/../firmware/firmware_endstops.bin",self.revision,self.printer.config,"/usr/bin/pasm")

        self.printer.path_planner = PathPlanner(self.printer, pru_firmware)
        self.printer.path_planner.acceleration = float(self.printer.config.get('Steppers', 'acceleration'))
        self.printer.acceleration = float(self.printer.config.get('Steppers', 'acceleration'))
        self.printer.path_planner.make_acceleration_tables()
        #self.printer.path_planner.save_acceleration_tables()
        #self.printer.path_planner.load_acceleration_tables()

        travel={}
        offset={}
        for axis in ['X','Y','Z']:
            travel[axis] = self.printer.config.getfloat('Geometry', 'travel_'+axis.lower())
            offset[axis] = self.printer.config.getfloat('Geometry', 'offset_'+axis.lower())

        self.printer.path_planner.travel_length = travel
        self.printer.path_planner.center_offset = offset
        self.printer.processor = GCodeProcessor(self.printer);

        # Set up communication channels
        self.printer.comms["USB"]    = USB(self.commands)
        self.printer.comms["Eth"]    = Ethernet(self.commands)
        self.printer.comms["Pipe_0"] = Pipe(self.commands, "Pipe_0")     # Pipe for Octoprint
        self.printer.comms["Pipe_1"] = Pipe(self.commands, "Pipe_1")     # Pipe for Toggle
        self.printer.comms["Pipe_2"] = Pipe(self.commands, "Pipe_2")     # Pipe for testing
        self.printer.comms["Pipe_2"].send_response = False     

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
                self.printer.reply(gcode)                
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
        if g.message == "ok" or g.code()=="ok" or g.code()=="No-Gcode":
            g.set_answer(None)
            return

        self.printer.processor.execute(g)
   
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

