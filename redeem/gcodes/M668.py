"""
GCode M668
Adjust backlash compensation for each named axis

M668 Xn Yn Zn En Hn An Bn Cn

Author: Anthony Clay
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from GCodeCommand import GCodeCommand
try:
    from Delta import Delta
except ImportError:
    from redeem.Delta import Delta
try:
    from Path import Path
except ImportError:
    from redeem.Path import Path

import logging


class M668(GCodeCommand):

    def execute(self, g):
        for index, axis in enumerate(["X", "Y", "Z", "E", "H", "A", "B", "C"]):
            if g.has_letter(axis):
                Path.backlash_compensation[index] = float(g.get_value_by_letter(axis))/1000.0 # Convert to meters.
                logging.info("Backlash compensation for axis " + str(axis) + " changed to " + str(Path.backlash_compensation[index]))

    def get_description(self):
        return "Adjust backlash compensation for each named axis"

