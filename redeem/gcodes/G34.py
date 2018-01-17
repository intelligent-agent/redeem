"""
GCode G34
Measure probe tip Z offset

Author: Matti Airas
email: mairas(at)iki(dot)fi
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
from __future__ import absolute_import

from .GCodeCommand import GCodeCommand
from redeem.Gcode import Gcode
import logging


class G34(GCodeCommand):

    def execute(self, g):

        # parse arguments

        # Get probe length (in mm), if present, else use config value
        if g.has_letter("D"):
            probe_length = g.get_float_by_letter("D")
        else:
            probe_length = 1000. * self.printer.config.getfloat('Probe',
                                                                'length')  # m
        # Get probe speed. If not preset, use config value.
        if g.has_letter("F"):
            probe_speed = g.get_float_by_letter("F") / 60000.0  # mm/min -> m/s
        else:
            probe_speed = self.printer.config.getfloat('Probe', 'speed')  # m/s

        # Get acceleration. If not present, use value from config.
        if g.has_letter("Q"):
            probe_accel = g.get_float_by_letter(
                "Q") / 3600000  # mm/min^2 -> m/s^2
        else:
            probe_accel = self.printer.config.getfloat(
                'Probe', 'accel')  # m/s^2

        probe_start_height = g.get_float_by_letter("Z", 5.0)

        # store the current Z coordinate
        point = self.printer.path_planner.get_current_pos(mm=True)
        orig_z = point["Z"]
        logging.debug("G34: orig_z = %f", orig_z)

        def exec_and_wait(cmd):
            G = Gcode({"message": cmd, "parent": g})
            self.printer.processor.execute(G)
            self.printer.path_planner.wait_until_done()

        # move up Z mm
        probe_start_z = orig_z + probe_start_height
        logging.debug("G34: moving up to Z=%f", probe_start_z)
        exec_and_wait("G0 Z{}".format(probe_start_z))

        # deploy probe
        logging.debug("G34: deploying probe")
        exec_and_wait("G32")

        probe_z = 1000. * self.printer.path_planner.probe(
            probe_length / 1000., probe_speed, probe_accel)

        # retract probe
        logging.debug("retracting probe")
        exec_and_wait("G31")

        # calculate the difference
        logging.debug("probe_z = %f", probe_z)
        z_offset = probe_z - orig_z
        logging.debug("z_offset = %f", z_offset)

        self.printer.send_message(
            g.prot,
            "Probe Z offset: {} mm".format(z_offset))

        # store the results
        if not g.has_letter("S"):
            self.printer.config.set('Probe', 'offset_z', str(z_offset / 1000.))

        logging.debug("Probe tip Z offset measurement finished")

    def get_description(self):
        return "Measure probe tip Z offset (height distance from print head)"

    def get_long_description(self):
        return """
Measure the probe tip Z offset, i.e., the height difference of probe tip
and the print head. Once the print head is moved to touch the bed, this command
lifts the head for Z mm, runs the G32 macro to deploy the probe, and
then probes down until the endstop is triggered. The height difference
is then stored as the [Probe] offset_z configuration parameter.

NOTE: G20 ignored. All units in mm.

Parameters:

Dn  Probe move maximum length n in mm
Fn  Probing speed n in mm/min
An  Probing acceleration n in mm/s^2
Zn  Upward move distance n in mm before probing (default: n = 5)
S   Simulate only (do not store the results)
        """

    def is_buffered(self):
        return True

    def is_async(self):
        return True
