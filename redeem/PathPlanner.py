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

        self.travel_length = {"X": 0.0, "Y": 0.0, "Z": 0.0, "E": 0.0, "H": 0.0}
        self.center_offset = {"X": 0.0, "Y": 0.0, "Z": 0.0, "E": 0.0, "H": 0.0}
        self.prev = G92Path({"X": 0.0, "Y": 0.0, "Z": 0.0, "E": 0.0, "H": 0.0}, 0)
        self.prev.set_prev(None)

        if pru_firmware:
            self.__init_path_planner()
        else:
            self.native_planner = None

    def __init_path_planner(self):
        self.native_planner = PathPlannerNative()

        self.native_planner.initPRU(self.pru_firmware.get_firmware(0),
                                    self.pru_firmware.get_firmware(1))

        self.native_planner.setPrintAcceleration(tuple([float(self.printer.acceleration[i]) for i in range(3)]))
        self.native_planner.setTravelAcceleration(tuple([float(self.printer.acceleration[i]) for i in range(3)]))
        self.native_planner.setAxisStepsPerMeter(tuple([long(Path.steps_pr_meter[i]) for i in range(3)]))
        self.native_planner.setMaxFeedrates(tuple([float(Path.max_speeds[i]) for i in range(3)]))	
        self.native_planner.setMaxJerk(self.printer.maxJerkXY / 1000.0, self.printer.maxJerkZ /1000.0)

        #Setup the extruders
        for i in range(Path.NUM_AXES - 3):
            e = self.native_planner.getExtruder(i)
            e.setMaxFeedrate(Path.max_speeds[i + 3])
            e.setPrintAcceleration(self.printer.acceleration[i + 3])
            e.setTravelAcceleration(self.printer.acceleration[i + 3])
            e.setMaxStartFeedrate(self.printer.maxJerkEH / 1000)
            e.setAxisStepsPerMeter(long(Path.steps_pr_meter[i + 3]))

        self.native_planner.setExtruder(0)

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

        path_back = {}
        path_center = {}
        path_zero = {}

        speed = Path.home_speed[0]

        for a in axis:
            if not self.printer.steppers[a].has_endstop:
                logging.debug("Skipping homing for " + str(a))
                continue
            logging.debug("Doing homing for " + str(a))
            logging.debug(self.travel_length)
            logging.debug(self.center_offset)
            path_back[a] = -self.travel_length[a]
            path_center[a] = -self.center_offset[a]
            path_zero[a] = 0
            speed = min(speed, Path.home_speed[Path.axis_to_index(a)])

            logging.debug("axis: "+str(a))

        # Move until endstop is hit
        p = RelativePath(path_back, speed, True)

        self.add_path(p)

        # Reset position to offset
        p = G92Path(path_center, speed)
        self.add_path(p)

        # Move to offset
        p = AbsolutePath(path_zero, speed)
        self.add_path(p)
        self.wait_until_done()
        logging.debug("homing done for " + str(axis))

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
            Path.axis_config = Path.AXIS_CONFIG_XY
            self._home_internal(axis)
            Path.axis_config = Path.AXIS_CONFIG_DELTA
        else:
            self._home_internal(axis)

    def probe(self):
        speed = Path.home_speed[0]
        path_back = {"Z": -self.travel_length["Z"]}
        # Move until endstop is hit
        p = RelativePath(path_back, speed, True)

        self.add_path(p)

        # TODO: return the position found when 
        # the Z-switch was hit. 
        return 0

    def add_path(self, new):
        """ Add a path segment to the path planner """
        # Link to the previous segment in the chain
        new.set_prev(self.prev)

        if new.needs_splitting():
            logging.debug("Path needs splitting")
            segments = new.get_delta_segments()
            for segment in segments:
                logging.debug("Adding "+str(segment))
                path = AbsolutePath(segment, self.printer.feed_rate * self.printer.factor)
                self.add_path(path)
            # Do not add the original segment
            new.unlink()
            return 

        if not new.is_G92():
            self.printer.ensure_steppers_enabled()
            #push this new segment   
            logging.debug("Pushing "+str(new.get_magnitude()))
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

    def queue_move(self, path):
        """ start of Python impl of queue_move """
        # Not working!
        path.primay_axis = np.max(path.delta)
        path.diff = path.delta * (1.0 / path.steps_pr_meter)

        path.steps_remaining = path.delta[path.primary_axis]
        path.xyz_dist = np.sqrt(np.dot(path.delta[:3], path.delta[:3]))
        path.distance = np.max(path.xyz_dist, path.diff[4])

        calculate_move(path)

    def calculate_move(self, path):
        """ Start of Python impl of calculate move """
        # Not working!
        axis_interval[4];
        speed = max(minimumSpeed,
                    path.speed) if path.is_x_or_y_move() else path.speed
        # time is in ticks
        path.time_in_ticks = time_for_move = F_CPU * path.distance / speed

        # Compute the slowest allowed interval (ticks/step), so maximum
        # feedrate is not violated
        axis_interval = abs(
            path.diff) * F_CPU / Path.max_speeds * path.steps_remaining
        limit_interval = max(np.max(axis_interval),
                             time_for_move / path.steps_remaining)

        path.full_interval = limit_interval

        # new time at full speed = limitInterval*p->stepsRemaining [ticks]
        time_for_move = limit_interval * path.steps_remaining;
        inv_time_s = F_CPU / time_for_move;

        axis_interval = time_for_move / path.delta;
        path.speed = sign(path.delta) * axis_diff * inv_time_s;


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
