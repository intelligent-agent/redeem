"""
GCode M665
Set delta arm calibration values

M665 L(diagonal rod length) R(delta radius)

Author: Anthony Clay
License: CC BY-SA: http://creativecommons.org/licenses/by-sa/2.0/
"""
from __future__ import absolute_import

from .GCodeCommand import GCodeCommand
from redeem.Delta import Delta


class M665(GCodeCommand):
    def execute(self, g):
        if g.num_tokens() == 0:
             g.set_answer("ok R: {}, L: {}".format(Delta.r, Delta.L))
        else:
            if g.has_letter("L"):
                Delta.L = g.get_float_by_letter("L")
            if g.has_letter("R"):
                Delta.r = g.get_float_by_letter("R")
                
            self.printer.path_planner.native_planner.delta_bot.setMainDimensions(Delta.L, Delta.r)
            # self.printer.path_planner.native_planner.delta_bot.recalculate()

    def get_description(self):
        return "Set delta arm calibration values"

    def get_long_description(self):
        return ("L sets the length of the arm. "
                "If the objects printed are too small, "
                "try increasing(?) the length of the arm\n"
                "R sets the radius of the towers. "
                "If the measured points are too convex, "
                "try increasing the radius")


