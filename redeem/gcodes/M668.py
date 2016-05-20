"""
GCode M668
Adjust backlash compensation for each named axis

M668 Xn Yn Zn En Hn An Bn Cn

Author: Anthony Clay
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from GCodeCommand import GCodeCommand

import logging


class M668(GCodeCommand):

    def execute(self, g):
        for index, axis in enumerate(["X", "Y", "Z", "E", "H", "A", "B", "C"]):
            if g.has_letter(axis):
                self.printer.backlash_compensation[index] = float(g.get_value_by_letter(axis))/1000.0 # Convert to meters.
                logging.info("Backlash compensation for axis " + str(axis) + " changed to " + str(self.printer.backlash_compensation[index]))
                self.printer.path_planner.update_backlash()

    def get_description(self):
        return "Adjust backlash compensation for each named axis"

