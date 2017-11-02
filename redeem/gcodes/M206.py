"""
GCode M206
Set home offset

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

from GCodeCommand import GCodeCommand
import logging

from redeem.Printer import Printer
from six import iteritems


class M206(GCodeCommand):

    def _get_offset_str(self):
        offsets = sorted(iteritems(self.printer.path_planner.center_offset))
        offset_strs = ["{}: {}".format(k, 1000. * v) for k, v
                       in offsets]
        return ", ".join(offset_strs)

    def execute(self, g):
        offset = self.printer.path_planner.center_offset
        if len(g.get_tokens()) == 0:
            # print out current offset values
            g.set_answer("ok " + self._get_offset_str())
        else:
            for axis in offset.keys():
                if g.has_letter(axis):
                    val = g.get_float_by_letter(axis)
                    g.remove_token_by_letter(axis)
                    adj = val / 1000.
                    if self.printer.axis_config == Printer.AXIS_CONFIG_DELTA:
                        # for delta, it's more logical if positive values
                        # raise the head
                        offset[axis] -= adj
                    else:
                        # for others, just do the simplest thing
                        offset[axis] += adj
                    logging.info("M206: Updated offset for %s to %f",
                                 axis, offset[axis])
            remaining = g.get_tokens()
            for tok in remaining:
                logging.warning("M206: Unknown axis: %s", tok[0])

    def get_description(self):
        return "Set or get end stop offsets"
    
    def get_long_description(self):
        return """
If no parameters are given, get the current end stop offsets.
To set the offset, provide the axes and their offset relative to
the current value. All values are in mm.

Example: M206 X0.1 Y-0.05 Z0.03"""
