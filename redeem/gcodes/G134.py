"""
GCode G134
Use the current position as offsets

Author: Elias Bakken
email: elias@iagent.no
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

import logging
from .GCodeCommand import GCodeCommand


class G134(GCodeCommand):

    def execute(self, g):

        # parse arguments
        if g.num_tokens() == 0:  # If no token is given, home all
            g.set_tokens(["X0", "Y0", "Z0"])

        logging.debug("Setting offsets for " + str(g.get_tokens()))

        # We want the ideal position to be used in the config
        self.printer.path_planner.wait_until_done()
        current_pos = self.printer.path_planner.get_current_pos(
            mm=False, ideal=True)

        for i in range(g.num_tokens()):  # Run through all tokens
            axis = g.token_letter(i)
            if axis.upper() in self.printer.AXES:
                # add the difference
                old = self.printer.path_planner.center_offset[axis.upper()]
                self.printer.path_planner.center_offset[axis.upper(
                )] += current_pos[axis.upper()]
                new = self.printer.path_planner.center_offset[axis.upper()]
                logging.debug("Updating offset for " + axis +
                              " from " + str(old) + " to " + str(new))
                self.printer.config.set('Geometry', 'offset_' + axis.lower(),
                                        str(self.printer.path_planner.center_offset[axis.upper()]))

    def get_description(self):
        return "Use the current head poition as offsets"

    def get_long_description(self):
        return """
After a G28 and then a G0 X0 Y0 Z0, jog the print head to where you want it to go after a G28. 
Then run this command. This will not allow you to position the head manually. 
You can not disable the steppers and move the ehad to where you want. 

This G-code operates on each axis. If no offsets are given, set the offset for x, y, z.
        """

    def is_buffered(self):
        return True
