"""
GCode M665
Set delta arm calibration values

M665 L(diagonal rod length) R(delta radius)

Author: Anthony Clay
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""

from GCodeCommand import GCodeCommand
try:
    from Delta import Delta
except ImportError:
    from redeem.Delta import Delta

import logging


class M665(GCodeCommand):
    def execute(self, g):
        if g.has_letter("L"):
            Delta.L = float(g.get_value_by_letter("L"))
        if g.has_letter("R"):
            Delta.r = float(g.get_value_by_letter("R"))
            
        self.printer.path_planner.native_planner.delta_bot.setMainDimensions(Delta.Hez, Delta.L, Delta.r)
        self.printer.path_planner.native_planner.delta_bot.recalculate()

    def get_description(self):
        return "Set delta arm calibration values"

    def get_long_description(self):
        return ("L sets the length of the arm. "
                "If the objects printed are too small, "
                "try increasing(?) the length of the arm"
                "R sets the radius of the towers. "
                "If the measured points are too convex, "
                "try increasing the radius")


