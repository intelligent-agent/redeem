"""
Printer class holding all printer components

Author: Mathieu Monney
email: zittix(at)xwaves(dot)net
Website: http://www.xwaves.net
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

from Path import Path


class Printer:
    """ A command received from pronterface or whatever """

    def __init__(self):
        self.steppers = {}
        self.heaters = {}
        self.thermistors = {}
        self.mosfets = {}
        self.end_stops = {}
        self.fans = []
        self.cold_ends = []
        self.coolers = []

        self.comms = {}  # Communication channels
        self.path_planner = None

        self.factor = 1.0
        self.extrude_factor = 1.0
        self.movement = Path.ABSOLUTE
        self.feed_rate = 0.5
        self.acceleration = [0.5]*8
        self.maxJerkXY = 20
        self.maxJerkZ = 1
        self.maxJerkEH = 4
        self.current_tool = "E"

        self.probe_points  = [{"X": 0, "Y": 0, "Z": 0}]*3
        self.probe_heights = [0]*3

    def ensure_steppers_enabled(self):
        """
        This method is called for every move, so it should be fast/cached.
        """
        for name, stepper in self.steppers.iteritems():
            if stepper.in_use and not stepper.enabled:
                # Stepper should be enabled, but is not.
                stepper.set_enabled(True)  # Force update

    def reply(self, gcode):
        """ Send a reply through the proper channel """
        if gcode.get_answer() is not None:
            self.send_message(gcode.prot, gcode.get_answer())

    def send_message(self, prot, msg):
        """ Send a message back to host """
        self.comms[prot].send_message(msg)
