"""
Path planner for Replicape. Just add paths to
this and they will be executed as soon as no other
paths are being executed.
It's a good idea to stack up maybe five path
segments, to have a buffer.

Author: Elias Bakken
email: elias(dot)bakken(at)gmail(dot)com
Website: http://www.thing-printer.com
License: GNU GPL v3: http://www.gnu.org/copyleft/gpl.html

 Redeem is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 Redeem is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with Redeem.  If not, see <http://www.gnu.org/licenses/>.
"""

import logging
from Path import Path, AbsolutePath, RelativePath, G92Path
from Delta import Delta
from Printer import Printer
import numpy as np
from PruInterface import PruInterface
from BedCompensation import BedCompensation

try:
    from pah_planner.PathPlannerNative import PathPlannerNative
except Exception, e:
    try:
        from _PathPlannerNative import PathPlannerNative
    except:
        logging.error("You have to compile the native path planner before running"
                  " Redeem. Make sure you have swig installed (apt-get "
                  "install swig) and run cd ../../PathPlanner/PathPlanner && "
                  "python setup.py install")
        raise e

class PathPlanner:

    def __init__(self, printer, pru_firmware):
        """ Init the planner """
        self.printer = printer
        self.steppers = printer.steppers
        self.pru_firmware = pru_firmware

        self.printer.path_planner = self

        self.travel_length  = {"X": 0, "Y": 0, "Z": 0, "E": 0, "H": 0, "A": 0, "B": 0, "C": 0}
        self.center_offset  = {"X": 0, "Y": 0, "Z": 0, "E": 0, "H": 0, "A": 0, "B": 0, "C": 0}
        self.home_pos       = {"X": 0, "Y": 0, "Z": 0, "E": 0, "H": 0, "A": 0, "B": 0, "C": 0}
        self.prev   = G92Path({"X": 0, "Y": 0, "Z": 0, "E": 0, "H": 0, "A": 0, "B": 0, "C": 0}, 0)
        self.prev.set_prev(None)

        if pru_firmware:
            self.__init_path_planner()
        else:
            self.native_planner = None

    def __init_path_planner(self):
        self.native_planner = PathPlannerNative(int(self.printer.move_cache_size))

        fw0 = self.pru_firmware.get_firmware(0)
        fw1 = self.pru_firmware.get_firmware(1)

        if fw0 is None or fw1 is None:
            return

        self.native_planner.initPRU(fw0, fw1)
        
        self.native_planner.setAxisStepsPerMeter(tuple(Path.steps_pr_meter))
        self.native_planner.setMaxSpeeds(tuple(Path.max_speeds))	
        self.native_planner.setMinSpeeds(tuple(Path.min_speeds))	
        self.native_planner.setAcceleration(tuple(Path.acceleration))
        self.native_planner.setJerks(tuple(Path.jerks))
        
        self.native_planner.setPrintMoveBufferWait(int(self.printer.print_move_buffer_wait))
        self.native_planner.setMinBufferedMoveTime(int(self.printer.min_buffered_move_time))
        self.native_planner.setMaxBufferedMoveTime(int(self.printer.max_buffered_move_time))
        
        self.native_planner.setSoftEndstopsMin(tuple(Path.soft_min))
        self.native_planner.setSoftEndstopsMax(tuple(Path.soft_max))
        
        self.native_planner.setBedCompensationMatrix(tuple(Path.matrix_bed_comp.ravel()))
        
        self.native_planner.setMaxPathLength(self.printer.max_length)
        
        self.native_planner.setAxisConfig(Path.axis_config)
        
        self.native_planner.delta_bot.setMainDimensions(Delta.Hez, Delta.L, Delta.r)
        self.native_planner.delta_bot.setEffectorOffset(Delta.Ae, Delta.Be, Delta.Ce)
        self.native_planner.delta_bot.setRadialError(Delta.A_radial, Delta.B_radial, Delta.C_radial);
        self.native_planner.delta_bot.setTangentError(Delta.A_tangential, Delta.B_tangential, Delta.C_tangential)
        self.native_planner.delta_bot.recalculate()
            
        self.native_planner.enableSlaves(Path.has_slaves)
        if Path.has_slaves:
            for master in Path.AXES:
                slave = Path.slaves[master]
                if slave:
                    master_index = Path.axis_to_index(master)
                    slave_index = Path.axis_to_index(slave)
                    self.native_planner.addSlave(int(master_index), int(slave_index))
                    logging.debug("Axis " + str(slave_index) + " is slaved to axis " + str(master_index))
                    
            
        self.native_planner.setBacklashCompensation(tuple(Path.backlash_compensation));
        
        self.native_planner.setState(tuple(Path.MAX_AXES*[0]))
        
        self.printer.plugins.path_planner_initialized(self)

        self.native_planner.runThread()

    def restart(self):
        self.native_planner.stopThread(True)        
        self.__init_path_planner()

    def update_steps_pr_meter(self):
        """ Update steps pr meter from the path """
        self.native_planner.setAxisStepsPerMeter(tuple(Path.steps_pr_meter))

    def get_current_pos(self, mm=False):
        """ Get the current pos as a dict """
        if mm:
            scale = 1000.0
        else:
            scale = 1.0
        state = self.native_planner.getState()
        pos = {}
        for index, axis in enumerate(Path.AXES[:Path.MAX_AXES]):
            pos[axis] = state[index]*scale
        return pos

    def get_extruder_pos(self, ext_nr):
        """ Return the current position of this extruder """
        state = self.native_planner.getState()
        return state[3+ext_nr]

    def wait_until_done(self):
        """ Wait until the queue is empty """
        self.native_planner.waitUntilFinished()

    def wait_until_sync_event(self):
        """ Blocks until a PRU sync event occurs """
        return (self.native_planner.waitUntilSyncEvent() > 0)

    def clear_sync_event(self):
        """ Resumes/Clears a pending sync event """
        self.native_planner.clearSyncEvent()

    def queue_sync_event(self, isBlocking):
       """ Returns True if a sync event has been queued. False on failure.(use wait_until_done() instead) """
       return self.native_planner.queueSyncEvent(isBlocking)

    def force_exit(self):
        self.native_planner.stopThread(True)

    def emergency_interrupt(self):
        """ Stop in emergency any moves. """
        # Note: This method has to be thread safe as it can be called from the
        # command thread directly or from the command queue thread
        self.native_planner.suspend()
        for name, stepper in self.printer.steppers.iteritems():
            stepper.set_disabled(True)

        #Create a new path planner to have everything clean when it restarts
        self.native_planner.stopThread(True)
        self.__init_path_planner()

    def suspend(self):
        ''' Temporary pause of planner '''
        self.native_planner.suspend()

    def resume(self):
        ''' resume a paused planner '''
        self.native_planner.resume()

    def _home_internal(self, axis):
        """ Private method for homing a set or a single axis """
        logging.debug("homing internal " + str(axis))
            
        path_search = {}
        path_backoff = {}
        path_fine_search = {}

        path_center = {}
        path_zero = {}

        speed = Path.home_speed[0] # TODO: speed for each axis
        accel = self.printer.acceleration[0] # TODO: accel for each axis

        for a in axis:
            if not self.printer.steppers[a].has_endstop:
                logging.debug("Skipping homing for " + str(a))
                continue
            logging.debug("Doing homing for " + str(a))
            if Path.home_speed[Path.axis_to_index(a)] < 0:
                # Search to positive ends
                path_search[a] = self.travel_length[a]
                path_center[a] = self.center_offset[a]
            else:
                # Search to negative ends
                path_search[a] = -self.travel_length[a]
                path_center[a] = -self.center_offset[a]

            backoff_length = -np.sign(path_search[a]) * Path.home_backoff_offset[Path.axis_to_index(a)]
            path_backoff[a] = backoff_length;
            path_fine_search[a] = -backoff_length * 1.2;
            
            speed = min(abs(speed), abs(Path.home_speed[Path.axis_to_index(a)]))
            fine_search_speed =  min(abs(speed), abs(Path.home_backoff_speed[Path.axis_to_index(a)]))
                    
        logging.debug("Search: %s" % path_search)
        logging.debug("Backoff to: %s" % path_backoff)
        logging.debug("Fine search: %s" % path_fine_search)
        logging.debug("Center: %s" % path_center)

        # Move until endstop is hit
        p = RelativePath(path_search, speed, accel, True, False, True, False)
        self.add_path(p)
        self.wait_until_done()
        logging.debug("Coarse search done!")

        # Reset position to offset
        p = G92Path(path_center)
        self.add_path(p)
        self.wait_until_done()

        # Back off a bit
        p = RelativePath(path_backoff, speed, accel, True, False, True, False)
        self.add_path(p)

        # Hit the endstop slowly
        p = RelativePath(path_fine_search, fine_search_speed, accel, True, False, True, False)
        self.add_path(p)
        self.wait_until_done()

        # Reset (final) position to offset
        p = G92Path(path_center)
        self.add_path(p)

        return path_center, speed
        
    def _go_to_home(self, axis):
        """
        go to the designated home position
        do this as a separate call from _home_internal due to delta platforms 
        performing home in cartesian mode
        """
        
        path_home = {}
        
        speed = Path.home_speed[0]
        accel = self.printer.acceleration[0]

        for a in axis:
            path_home[a] = self.home_pos[a]
            speed = min(abs(speed), abs(Path.home_speed[Path.axis_to_index(a)]))
            
        logging.debug("Home: %s" % path_home)
            
        # Move to home position
        p = AbsolutePath(path_home, speed, accel, True, False, False, False)
        
        self.add_path(p)
        self.wait_until_done()
        
        # Due to rounding errors, we explicitly set the found 
        # position to the right value. 
        # Reset (final) position to offset
        p = G92Path(path_home)
        self.add_path(p)

        return

    def home(self, axis):
        """ Home the given axis using endstops (min) """
        logging.debug("homing " + str(axis))

        # Home axis for core X,Y and H-Belt independently to avoid hardware
        # damages.
        if Path.axis_config == Path.AXIS_CONFIG_CORE_XY or \
                        Path.axis_config == Path.AXIS_CONFIG_H_BELT:
            for a in axis:
                self._home_internal(a)
        # For delta, switch to cartesian when homing
        elif Path.axis_config == Path.AXIS_CONFIG_DELTA:
            if 0 < len({"X", "Y", "Z"}.intersection(set(axis))) < 3:
                axis = list(set(axis).union({"X", "Y", "Z"}))	# Deltas must home all axes.
            Path.axis_config = Path.AXIS_CONFIG_XY
            path_center, speed = self._home_internal(axis)
            Path.axis_config = Path.AXIS_CONFIG_DELTA

            # homing was performed in cartesian mode
            # need to convert back to delta

            Az = path_center['X']
            Bz = path_center['Y']
            Cz = path_center['Z']
            
            z_offset = self.native_planner.delta_bot.vertical_offset(Az,Bz,Cz) # vertical offset
            xyz = self.native_planner.delta_bot.forward_kinematics(Az, Bz, Cz) # effector position
            xyz[2] += z_offset
            path = {'X':xyz[0], 'Y':xyz[1], 'Z':xyz[2]}
            
            logging.debug("Delta Home: " + str(xyz))
            
            p = G92Path(path)
            self.add_path(p)
            self.wait_until_done()
            
        else: # AXIS_CONFIG_XY
            self._home_internal(axis)
            
        # go to the designated home position
        self._go_to_home(axis)

        # Reset backlash compensation
        self.native_planner.resetBacklash()

        logging.debug("homing done for " + str(axis))
            
        return

    def probe(self, z, speed, accel):
        self.wait_until_done()
        
        self.printer.ensure_steppers_enabled()
        
        # save the starting position
        start = self.get_current_pos()
        
        # calculate how many steps the requested z movement will require
        steps = np.ceil(z*Path.steps_pr_meter[2])
        z_dist = steps/Path.steps_pr_meter[2]
        logging.debug("Steps total: "+str(steps))
        
        # select the relative end point
        # this is not axis_config dependent as we are not swapping 
        # axis_config like we do when homing
        end   = {"Z":-z_dist}
        
        # add a relative move to the path planner
        # this tells the head to move down a set distance
        # the probe end-stop should be triggered during this move
        path = RelativePath(end, speed, accel, 
                            cancelable=True, 
                            use_bed_matrix=False, 
                            use_backlash_compensation=True, 
                            enable_soft_endstops=False)
        self.add_path(path)
        self.wait_until_done()

        # get the number of steps that we haven't done 
        steps_remaining = PruInterface.get_steps_remaining()
        logging.debug("Steps remaining : "+str(steps_remaining))

        # Calculate how many steps the Z axis moved
        steps -= steps_remaining
        z_dist = steps/Path.steps_pr_meter[2]
        
        # make a move to take us back to where we started
        end   = {"Z":z_dist}
        path = RelativePath(end, speed, accel, 
                            cancelable=True, 
                            use_bed_matrix=False, 
                            use_backlash_compensation=True, 
                            enable_soft_endstops=False)
        self.add_path(path)
        self.wait_until_done()
        
        # reset position back to  where we actually are
        path = G92Path(start)
        
        self.add_path(path)
        self.wait_until_done()
        
        return -z_dist
        
    def update_autolevel_matrix(self, probe_points, probe_heights):
        """
        updates the bed compensation matrix
        """
        
        logging.debug("updating bed compensation matrix")        
        logging.debug("Probe points = " + str(probe_points))
        logging.debug("Probe heights = " + str(probe_heights))
        
        Path.matrix_bed_comp = BedCompensation.create_rotation_matrix(probe_points, probe_heights)
        
        self.native_planner.setBedCompensationMatrix(tuple(Path.matrix_bed_comp.ravel()))
        
        return

    def add_path(self, new):
        """ Add a path segment to the path planner """
        """ This code, and the native planner, needs to be updated for reach. """
        # Link to the previous segment in the chain    
        
        new.set_prev(self.prev)
        
        # NOTE: printing the added path slows things down SIGNIFICANTLY
        #logging.debug("path added: "+ str(new))
        
        if new.is_G92():
            self.native_planner.setState(tuple(new.end_pos))
        elif new.needs_splitting():
            #TODO: move this to C++
            # this branch splits up any G2 or G3 movements (arcs)
            # should be moved to C++ as it is math heavy
            # need to convert it to linear segments before feeding to the queue
            # as we want to keep the queue only dealing with linear stuff for simplicity
            for seg in new.get_segments():
                self.add_path(seg)
            
        else:
            self.printer.ensure_steppers_enabled() 
            
            optimize = new.movement != Path.RELATIVE
            tool_axis = Path.axis_to_index(self.printer.current_tool)
            
            self.native_planner.setAxisConfig(int(Path.axis_config))
            
            self.native_planner.queueMove(tuple(new.start_pos),
                                      tuple(new.end_pos), 
                                      new.speed, 
                                      new.accel,
                                      bool(new.cancelable),
                                      bool(optimize),
                                      bool(new.enable_soft_endstops),
                                      bool(new.use_bed_matrix),
                                      bool(new.use_backlash_compensation), 
                                      int(tool_axis), 
                                      True)

        self.prev = new
        self.prev.unlink()  # We don't want to store the entire print
                            # in memory, so we keep only the last path.

    def set_extruder(self, ext_nr):
        """
        TODO: does this function do anything? Should it be setting the tool axis?
        """
        if ext_nr in range(Path.MAX_AXES-3):
            logging.debug("Selecting "+str(ext_nr))
            #Path.steps_pr_meter[3] = self.printer.steppers[
            #        Path.index_to_axis(ext_nr+3)
            #        ].get_steps_pr_meter()
            #self.native_planner.setExtruder(ext_nr)


if __name__ == '__main__':
    import numpy as np
    import os
    from CascadingConfigParser import CascadingConfigParser

    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%m-%d %H:%M')

    from Stepper import Stepper, Stepper_00B1
    from PruFirmware import PruFirmware

    Path.steps_pr_meter = np.array(
        [3.125 * (2 ** 4) * 1000.0, 3.125 * (2 ** 4) * 1000.0,
         133.33333333 * (2 ** 4) * 1000.0, 33.4375 * (2 ** 4) * 1000.0,
         33.4375 * (2 ** 4) * 1000.0])

    print "Making steppers"

    steppers = {}

    steppers["X"] = Stepper_00B1("GPIO0_27", "GPIO1_29", "GPIO2_4", 11, 0, "X", 0, 0)
    steppers["X"].set_microstepping(2)
    steppers["X"].set_steps_pr_mm(6.0)
    steppers["Y"] = Stepper_00B1("GPIO1_12", "GPIO0_22", "GPIO2_5", 12, 1, "Y", 1, 1)
    steppers["Y"].set_microstepping(2)
    steppers["Y"].set_steps_pr_mm(6.0)
    steppers["Z"] = Stepper_00B1("GPIO0_23", "GPIO0_26", "GPIO0_15", 13, 2, "Z", 2, 2)
    steppers["Z"].set_microstepping(2)
    steppers["Z"].set_steps_pr_mm(160.0)
    steppers["E"] = Stepper_00B1("GPIO1_28", "GPIO1_15", "GPIO2_1", 14, 3, "E", 3, 3)
    steppers["E"].set_microstepping(2)
    steppers["E"].set_steps_pr_mm(5.0)
    steppers["H"] = Stepper_00B1("GPIO1_13", "GPIO1_14", "GPIO2_3", 15, 4, "H", 4, 4)
    steppers["H"].set_microstepping(2)
    steppers["H"].set_steps_pr_mm(5.0)

    printer = Printer()

    printer.steppers = steppers

    # Parse the config
    printer.config = CascadingConfigParser(
        ['configs/default.cfg'])

    # Get the revision from the Config file
    printer.config.parse_capes()
    revision = printer.config.replicape_revision
    
    dirname = os.path.dirname(os.path.realpath(__file__))
    Path.set_axes(5)

    path_planner = PathPlanner(printer, None)

    speed = 3000 / 60000.0

    path_planner.add_path(AbsolutePath(
        {
            "X": 0.01
        }, speed))

    path_planner.add_path(AbsolutePath(
        {
            "X": 0.0
        }, speed))

    path_planner.wait_until_done()

    path_planner.force_exit()
