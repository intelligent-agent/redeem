'''
Path planner for Replicape. Just add paths to
this and they will be executed as soon as no other
paths are being executed.
It's a good idea to stack up maybe five path
segments, to have a buffer.

Author: Elias Bakken
email: elias(dot)bakken(at)gmail(dot)com
Website: http://www.thing-printer.com
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
'''

import time
import logging
from Path2 import Path, AbsolutePath, RelativePath, G92Path
import numpy as np
from Printer import Printer
from PathPlannerNative import PathPlannerNative
import threading
import Queue



class PathPlanner:
    ''' Init the planner '''
    def __init__(self, printer, pru_firmware):
        self.printer        = printer
        self.steppers       = printer.steppers


        self.travel_length  = {"X":0.0, "Y":0.0, "Z":0.0}
        self.center_offset  = {"X":0.0, "Y":0.0, "Z":0.0}
        self.prev           =  G92Path({"X":0.0, "Y":0.0, "Z":0.0, "E":0.0,"H":0.0}, 0)
        self.prev.set_prev(None)
 
        if pru_firmware:
            self.native_planner = PathPlannerNative()

            self.native_planner.initPRU( pru_firmware.get_firmware(0), pru_firmware.get_firmware(1))

            s = (long(Path.steps_pr_meter[0]),long(Path.steps_pr_meter[1]),long(Path.steps_pr_meter[2]),long(Path.steps_pr_meter[3]))
            self.native_planner.setAxisStepsPerMeter(s)
            

            self.native_planner.runThread()

    ''' Get the current pos as a dict '''
    def get_current_pos(self):
        pos = np.zeros(Path.NUM_AXES)
        if self.prev:
            pos = self.prev.end_pos        
        pos2 = {}
        for index, axis in enumerate(Path.AXES):
            pos2[axis] = pos[index]

        return pos2
          
    def wait_until_done(self):
        """ Wait until the queue is empty """
        self.native_planner.waitUntilFinished()

    def force_exit(self):
        self.native_planner.stopThread(True)

    ''' Home the given axis using endstops (min) '''
    def home(self,axis):
        return 

        if axis=="E" or axis=="H":
            return

        logging.debug("homing "+axis)
        speed = Path.home_speed[Path.axis_to_index(axis)]
        # Move until endstop is hit
        p = RelativePath({axis:-self.travel_length[axis]}, speed, self.printer.acceleration)
        self.add_path(p)

        # Reset position to offset
        p = G92Path({axis:-self.center_offset[axis]}, speed)
        self.add_path(p)
        
        # Move to offset
        p = AbsolutePath({axis:0}, speed, self.printer.acceleration)
        self.add_path(p)
        self.finalize_paths()
        self.wait_until_done()
        logging.debug("homing done for "+axis)

    ''' Add a path segment to the path planner '''        
    def add_path(self, new):   

        # Link to the previous segment in the chain
        new.set_prev(self.prev)
        
        logging.debug("Adding path "+str(new))
        #logging.debug("Previous path was "+str(self.prev))

        if new.is_G92():
            pass #FIXME: Flush the path in the planner or tell the planner it's a G92.... I dont know actually...
        else:
            #push this new segment
            #unit for speed is mm/s
            #unit for position is in mm
 
            speed = new.speed*1000.0
            start = new.start_pos * 1000
            end = new.end_pos * 1000

            self.native_planner.queueMove((start[0],start[1],start[2],start[3]),(end[0],end[1],end[2],end[3]),speed)

        logging.debug("Path added.")
        self.prev = new

    



if __name__ == '__main__':
    import cProfile
    import numpy as np
    import os
    import sys
    from CascadingConfigParser import CascadingConfigParser

    logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M')


    from Stepper import Stepper
    from Gcode import Gcode
    from PruFirmware import PruFirmware


    Path.steps_pr_meter = np.array([3.125*(2**4)*1000.0, 3.125*(2**4)*1000.0, 133.33333333*(2**4)*1000.0, 33.4375*(2**4)*1000.0, 33.4375*(2**4)*1000.0])
        
    
    print "Making steppers"


    steppers = {}
    steppers["X"] = Stepper("GPIO0_27", "GPIO1_29", "GPIO2_4",  0, "X",None,0,0)
    steppers["X"].set_microstepping(2)
    steppers["X"].set_steps_pr_mm(6.0)
    steppers["Y"] = Stepper("GPIO1_12", "GPIO0_22", "GPIO2_5",  1, "Y",None,1,1)  
    steppers["Y"].set_microstepping(2)
    steppers["Y"].set_steps_pr_mm(6.0)
    steppers["Z"] = Stepper("GPIO0_23", "GPIO0_26", "GPIO0_15", 2, "Z",None,2,2)  
    steppers["Z"].set_microstepping(2)
    steppers["Z"].set_steps_pr_mm(160.0)
    steppers["E"] = Stepper("GPIO1_28", "GPIO1_15", "GPIO2_1",  3, "Ext1",None,3,3)
    steppers["E"].set_microstepping(2)
    steppers["E"].set_steps_pr_mm(5.0)
    steppers["H"] = Stepper("GPIO1_13", "GPIO1_14", "GPIO2_3",  4, "Ext2",None,4,4)
    steppers["H"].set_microstepping(2)
    steppers["H"].set_steps_pr_mm(5.0)

    printer = Printer()

    printer.steppers = steppers

    # Parse the config
    printer.config = CascadingConfigParser(['/etc/redeem/default.cfg', '/etc/redeem/local.cfg'])

    # Get the revision from the Config file
    revision = printer.config.get('System', 'revision', "A4")
  

    dirname = os.path.dirname(os.path.realpath(__file__))

    pru_firmware = PruFirmware(dirname+"/../firmware/firmware_runtime.p",dirname+"/../firmware/firmware_runtime.bin",dirname+"/../firmware/firmware_endstops.p",dirname+"/../firmware/firmware_endstops.bin",revision,printer.config,"/usr/bin/pasm")


    path_planner = PathPlanner(printer, pru_firmware)

    speed=3000/60000.0
    acceleration = 0.5

    path_planner.add_path(AbsolutePath(
    {
        "X": 0.01
    }, speed, acceleration))

    path_planner.add_path(AbsolutePath(
    {
        "X": 0.0
    }, speed, acceleration))
   
    path_planner.wait_until_done()

    path_planner.force_exit()


