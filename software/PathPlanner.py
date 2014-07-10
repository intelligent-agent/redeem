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
from Path import Path, AbsolutePath, RelativePath, G92Path
import numpy as np
from Printer import Printer
import threading
import Queue

try:
    from path_planner.PathPlannerNative import PathPlannerNative
except Exception, e:
    logging.error("You have to compile the native path planner before running Redeem. Make sure you have swig installed (apt-get install swig) and run cd ../../PathPlanner/PathPlanner && python setup.py install")
    raise e

class PathPlanner:
    ''' Init the planner '''
    def __init__(self, printer, pru_firmware):
        self.printer        = printer
        self.steppers       = printer.steppers
        self.pru_firmware   = pru_firmware

        self.travel_length  = {"X":0.0, "Y":0.0, "Z":0.0}
        self.center_offset  = {"X":0.0, "Y":0.0, "Z":0.0}
        self.prev           =  G92Path({"X":0.0, "Y":0.0, "Z":0.0, "E":0.0,"H":0.0}, 0)
        self.prev.set_prev(None)
 
        if pru_firmware:
            self.__init_path_planner()

    def __init_path_planner(self):
        self.native_planner = PathPlannerNative()

        self.native_planner.initPRU( self.pru_firmware.get_firmware(0), self.pru_firmware.get_firmware(1))

        self.native_planner.setPrintAcceleration(tuple([float(self.printer.acceleration) for i in range(3)]))
        self.native_planner.setTravelAcceleration(tuple([float(self.printer.acceleration) for i in range(3)]))
        self.native_planner.setAxisStepsPerMeter(tuple([long(Path.steps_pr_meter[i]) for i in range(3)]))
        self.native_planner.setMaxFeedrates(tuple([float(Path.max_speeds[i]) for i in range(3)]))
        self.native_planner.setMaxJerk(20/1000.0,0.3/1000.0)
        
        #Setup the extruders
        for i in range(Path.NUM_AXES-3):
            e = self.native_planner.getExtruder(i)
            e.setMaxFeedrate(Path.max_speeds[i+3])
            e.setPrintAcceleration(self.printer.acceleration)
            e.setTravelAcceleration(self.printer.acceleration)
            e.setMaxStartFeedrate(0.04)
            e.setAxisStepsPerMeter(long(Path.steps_pr_meter[i+3]))

        self.native_planner.setExtruder(0)

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

    def emergency_interrupt(self):
        """ Stop in emergency any moves. """
        # Note: This method has to be thread safe as it can be called from the command thread directly or from the command queue thread
        self.native_planner.suspend()
        for name, stepper in self.printer.steppers.iteritems():
            stepper.set_disabled(True)

        #Create a new path planner to have everything clean when it restarts
        self.native_planner.stopThread(True)
        self.__init_path_planner()


    def suspend(self):
        self.native_planner.suspend()

    def resume(self):
        self.native_planner.resume()

    ''' Private method for homing a set or a single axis '''
    def _home_internal(self, axis):

        logging.debug("homing "+str(axis))

        path_back={}
        path_center={}
        path_zero={}
        
        speed = Path.home_speed[0]

        for a in axis:

            if a == 'E' or a == 'H':
                continue

            path_back[a] = -self.travel_length[a]
            path_center[a] = -self.center_offset[a]
            path_zero[a] = 0
            speed = min(speed, Path.home_speed[Path.axis_to_index(a)])

         # Move until endstop is hit
        p = RelativePath(path_back, speed, self.printer.acceleration, True)
        
        self.add_path(p)

        # Reset position to offset
        p = G92Path(path_center, speed)
        self.add_path(p)
        
        # Move to offset
        p = AbsolutePath(path_zero, speed, self.printer.acceleration)
        self.add_path(p)
        self.wait_until_done()
        logging.debug("homing done for "+str(axis))

    ''' Home the given axis using endstops (min) '''
    def home(self, axis):

        logging.debug("homing "+str(axis))

        # Home axis for core X,Y and H-Belt independently to avoid hardware dammages.
        if Path.axis_config == Path.AXIS_CONFIG_CORE_XY or Path.axis_config == Path.AXIS_CONFIG_H_BELT:
            for a in axis:
                self._home_internal(a)
        else:
            self._home_internal(axis)

    ''' Add a path segment to the path planner '''        
    def add_path(self, new):   

        # Link to the previous segment in the chain
        new.set_prev(self.prev)

        if not new.is_G92():
            #push this new segment
            self.native_planner.queueMove(tuple(new.delta[:4]), tuple(new.num_steps[:4]), new.speed, bool(new.cancelable), bool(new.movement != Path.RELATIVE))
            #self.native_planner.queueMove(tuple(start),tuple(end), new.speed, bool(new.cancelable), True if new.movement != Path.RELATIVE else False,tuple(steps))

        self.prev = new
        self.prev.unlink() # We don't want to store the entire print 
                           # in memory, so we keep only the last path.

    def set_extruder(self, ext_nr):
        if ext_nr in [0, 1]:
            self.native_planner.setExtruder(ext_nr)


    ''' start of Python impl of queue_move '''
    # Not working!
    def queue_move(self, path):
        path.primay_axis     = np.max(path.delta)
        path.diff            = path.delta*(1.0/path.steps_pr_meter)

        path.steps_remaining = path.delta[path.primary_axis]
        path.xyz_dist        = np.sqrt(np.dot(path.delta[:3],path.delta[:3]))
        path.distance        = np.max(path.xyz_dist, path.diff[4])

        calculate_move(path)        

    ''' Start of Python impl of calculate move '''
    # Not working!
    def caluculate_move(self, path):
        axis_interval[4];
        speed = max(minimumSpeed, path.speed) if path.is_x_or_y_move() else path.speed
        path.time_in_ticks = time_for_move = F_CPU * path.distance / speed # time is in ticks
        
        # Compute the slowest allowed interval (ticks/step), so maximum feedrate is not violated
        axis_interval = abs(path.diff)*F_CPU / Path.max_speeds*path.steps_remaining #
        limit_interval = max(np.max(axis_interval), time_for_move/path.steps_remaining) 
    
        path.full_interval = limit_interval

        # new time at full speed = limitInterval*p->stepsRemaining [ticks]
        time_for_move = limit_interval * path.steps_remaining; 
        inv_time_s = F_CPU / time_for_move;

        axis_interval   = time_for_move / path.delta;
        path.speed      = sign(path.delta) * axis_diff * inv_time_s;



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

