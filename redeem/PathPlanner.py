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
from Path import Path, CompensationPath, AbsolutePath, RelativePath, G92Path
from Delta import Delta
from Printer import Printer
import numpy as np

try:
    from path_planner.PathPlannerNative import PathPlannerNative
except Exception, e:
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

        self.travel_length = {"X": 0.0, "Y": 0.0, "Z": 0.0, "E": 0.0, "H": 0.0}
        self.center_offset = {"X": 0.0, "Y": 0.0, "Z": 0.0, "E": 0.0, "H": 0.0}
        self.home_pos = {"X": 0.0, "Y": 0.0, "Z": 0.0, "E": 0.0, "H": 0.0}
        self.prev = G92Path({"X": 0.0, "Y": 0.0, "Z": 0.0, "E": 0.0, "H": 0.0}, 0)
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

        self.native_planner.setPrintAcceleration(tuple([float(self.printer.acceleration[i]) for i in range(3)]))
        self.native_planner.setTravelAcceleration(tuple([float(self.printer.acceleration[i]) for i in range(3)]))
        self.native_planner.setAxisStepsPerMeter(tuple([long(Path.steps_pr_meter[i]) for i in range(3)]))
        self.native_planner.setMaxFeedrates(tuple([float(Path.max_speeds[i]) for i in range(3)]))	
        self.native_planner.setMaxJerk(self.printer.maxJerkXY / 1000.0, self.printer.maxJerkZ /1000.0)
        self.native_planner.setPrintMoveBufferWait(int(self.printer.print_move_buffer_wait))
        self.native_planner.setMinBufferedMoveTime(int(self.printer.min_buffered_move_time))
        self.native_planner.setMaxBufferedMoveTime(int(self.printer.max_buffered_move_time))
        

        #Setup the extruders
        for i in range(Path.NUM_AXES - 3):
            e = self.native_planner.getExtruder(i)
            e.setMaxFeedrate(Path.max_speeds[i + 3])
            e.setPrintAcceleration(self.printer.acceleration[i + 3])
            e.setTravelAcceleration(self.printer.acceleration[i + 3])
            e.setMaxStartFeedrate(self.printer.maxJerkEH / 1000)
            e.setAxisStepsPerMeter(long(Path.steps_pr_meter[i + 3]))
            e.setDirectionInverted(False)

        self.native_planner.setExtruder(0)
        self.native_planner.setDriveSystem(Path.axis_config)
        logging.info("Setting drive system to "+str(Path.axis_config))

        self.printer.plugins.path_planner_initialized(self)

        self.native_planner.runThread()

    def get_current_pos(self):
        """ Get the current pos as a dict """
        pos = self.prev.end_pos
        pos2 = {}
        for index, axis in enumerate(Path.AXES[:Path.NUM_AXES]):
            pos2[axis] = pos[index]
        return pos2

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

    def fire_sync_event(self):
        """ Unclogs any threads waiting for a sync """
        

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
        self.native_planner.suspend()

    def resume(self):
        self.native_planner.resume()

    def _home_internal(self, axis):
        """ Private method for homing a set or a single axis """
        logging.debug("homing internal " + str(axis))
            

        path_search = {}
        path_backoff = {}
        path_fine_search = {}

        path_center = {}
        path_zero = {}

        speed = Path.home_speed[0]

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
            
            logging.debug("axis: "+str(a))
        
        logging.debug("Search: %s" % path_search)
        logging.debug("Backoff to: %s" % path_backoff)
        logging.debug("Fine search: %s" % path_fine_search)
        logging.debug("Center: %s" % path_center)

        # Move until endstop is hit
        p = RelativePath(path_search, speed, True, False, True, False)
        self.add_path(p)
        self.wait_until_done()

        # Reset position to offset
        p = G92Path(path_center, speed)
        self.add_path(p)
        self.wait_until_done()

        # Back off a bit
        p = RelativePath(path_backoff, speed, True, False, True, False)
        self.add_path(p)

        # Hit the endstop slowly
        p = RelativePath(path_fine_search, fine_search_speed, True, False, True, False)
        self.add_path(p)
        self.wait_until_done()

        # Reset (final) position to offset
        p = G92Path(path_center, speed)
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

        for a in axis:
            path_home[a] = self.home_pos[a]
            speed = min(abs(speed), abs(Path.home_speed[Path.axis_to_index(a)]))
            
        logging.debug("Home: %s" % path_home)
            
        # Move to home position
        p = AbsolutePath(path_home, speed, True, False, False, False)
        self.add_path(p)
        self.wait_until_done()
        
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
            
            z_offset = Delta.vertical_offset(Az,Bz,Cz) # vertical offset
            xyz = Delta.forward_kinematics2(Az, Bz, Cz) # effector position
            xyz[2] += z_offset
            path = {'X':xyz[0], 'Y':xyz[1], 'Z':xyz[2]}
            
            p = G92Path(path, speed)
            self.add_path(p)
            self.wait_until_done()
            
        else:
            self._home_internal(axis)
            
        # go to the designated home position
        self._go_to_home(axis)

        # Reset backlash compensation
        Path.backlash_reset()

        logging.debug("homing done for " + str(axis))
            
        return

    def probe(self, z):
        old_feedrate = self.printer.feed_rate # Save old feedrate

        speed = Path.home_speed[0]
        path_back = {"Z": -z}
        # Move until endstop is hits
        p = RelativePath(path_back, speed, True)

        self.wait_until_done()
        self.add_path(p)
        self.wait_until_done()

        self.printer.feed_rate = old_feedrate

        import struct
        import mmap

        PRU_ICSS = 0x4A300000 
        PRU_ICSS_LEN = 512*1024

        RAM2_START = 0x00012000

        with open("/dev/mem", "r+b") as f:	       
            ddr_mem = mmap.mmap(f.fileno(), PRU_ICSS_LEN, offset=PRU_ICSS) 
            shared = struct.unpack('LLLL', ddr_mem[RAM2_START:RAM2_START+16])
            steps_remaining = shared[3]
        logging.info("Steps remaining : "+str(steps_remaining))

        # Update the current Z-position based on the probing
        delta_z = steps_remaining/Path.steps_pr_meter[2]

        return delta_z

    def add_path(self, new):
        """ Add a path segment to the path planner """
        """ This code, and the native planner, needs to be updated for reach. """
        # Link to the previous segment in the chain
        new.set_prev(self.prev)

        if new.compensation is not None:
            # Apply a backlash compensation move
#           CompensationPath(new.compensation, new.speed, False, False, False))
            self.native_planner.queueMove(tuple(np.zeros(Path.NUM_AXES)[:4]),
                                          tuple(new.compensation[:4]), new.speed,
                                          bool(new.cancelable),
                                          False)

        if new.needs_splitting():
            path_batch = new.get_delta_segments()
            # Construct a batch
            batch_array = np.zeros(shape=(len(path_batch)*2*4),dtype=np.float64)     # Change this to reflect NUM_AXIS.
         
            for maj_index, path in enumerate(path_batch):
                for subindex in range(4):  # this needs to be NUM_AXIS
                    batch_array[(maj_index * 8) + subindex] = path.start_pos[subindex]
                    batch_array[(maj_index * 8) + 4 + subindex] = path.stepper_end_pos[subindex]
                
                self.prev = path
                self.prev.unlink()

            # Queue the entire batch at once.
            self.printer.ensure_steppers_enabled()
            self.native_planner.queueBatchMove(batch_array, new.speed, bool(new.cancelable), bool(True))
                
            # Do not add the original segment
            new.unlink()
            return 

        if not new.is_G92():
            self.printer.ensure_steppers_enabled()
            #push this new segment   
            self.native_planner.queueMove(tuple(new.start_pos[:4]),
                                      tuple(new.stepper_end_pos[:4]), new.speed,
                                      bool(new.cancelable),
                                      bool(new.movement != Path.RELATIVE))

        self.prev = new
        self.prev.unlink()  # We don't want to store the entire print
                            # in memory, so we keep only the last path.

    def set_extruder(self, ext_nr):
        if ext_nr in range(Path.NUM_AXES-3):
            logging.debug("Selecting "+str(ext_nr))
            Path.steps_pr_meter[3] = self.printer.steppers[
                    Path.index_to_axis(ext_nr+3)
                    ].get_steps_pr_meter()
            self.native_planner.setExtruder(ext_nr)


if __name__ == '__main__':
    import numpy as np
    import os
    from CascadingConfigParser import CascadingConfigParser

    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%m-%d %H:%M')

    from Stepper import Stepper
    from PruFirmware import PruFirmware

    Path.steps_pr_meter = np.array(
        [3.125 * (2 ** 4) * 1000.0, 3.125 * (2 ** 4) * 1000.0,
         133.33333333 * (2 ** 4) * 1000.0, 33.4375 * (2 ** 4) * 1000.0,
         33.4375 * (2 ** 4) * 1000.0])

    print "Making steppers"

    steppers = {}
    steppers["X"] = Stepper("GPIO0_27", "GPIO1_29", "GPIO2_4", 0, "X", None, 0,
                            0)
    steppers["X"].set_microstepping(2)
    steppers["X"].set_steps_pr_mm(6.0)
    steppers["Y"] = Stepper("GPIO1_12", "GPIO0_22", "GPIO2_5", 1, "Y", None, 1,
                            1)
    steppers["Y"].set_microstepping(2)
    steppers["Y"].set_steps_pr_mm(6.0)
    steppers["Z"] = Stepper("GPIO0_23", "GPIO0_26", "GPIO0_15", 2, "Z", None,
                            2, 2)
    steppers["Z"].set_microstepping(2)
    steppers["Z"].set_steps_pr_mm(160.0)
    steppers["E"] = Stepper("GPIO1_28", "GPIO1_15", "GPIO2_1", 3, "Ext1", None,
                            3, 3)
    steppers["E"].set_microstepping(2)
    steppers["E"].set_steps_pr_mm(5.0)
    steppers["H"] = Stepper("GPIO1_13", "GPIO1_14", "GPIO2_3", 4, "Ext2", None,
                            4, 4)
    steppers["H"].set_microstepping(2)
    steppers["H"].set_steps_pr_mm(5.0)

    printer = Printer()

    printer.steppers = steppers

    # Parse the config
    printer.config = CascadingConfigParser(
        ['/etc/redeem/default.cfg', '/etc/redeem/local.cfg'])

    # Get the revision from the Config file
    revision = printer.config.get('System', 'revision', "A4")

    dirname = os.path.dirname(os.path.realpath(__file__))

    pru_firmware = PruFirmware(dirname + "/../firmware/firmware_runtime.p",
                               dirname + "/../firmware/firmware_runtime.bin",
                               dirname + "/../firmware/firmware_endstops.p",
                               dirname + "/../firmware/firmware_endstops.bin",
                               revision, printer.config, "/usr/bin/pasm")

    path_planner = PathPlanner(printer, pru_firmware)

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
